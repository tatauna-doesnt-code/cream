"""Version-aware Painter adapter. Every function runs on the UI thread."""
import copy
from pathlib import Path

import substance_painter as sp
import substance_painter.export
import substance_painter.project
import substance_painter.textureset

from .core import dimensions
from . import tm_text, compatibility

if compatibility.current().customization:
    import substance_painter.colormanagement
    import substance_painter.layerstack
    import substance_painter.source


def project_path():
    if not sp.project.is_open() or not sp.project.file_path():
        raise ValueError("Open a saved .spp project before continuing.")
    return str(Path(sp.project.file_path()).resolve())


def ready():
    return sp.project.is_open() and sp.project.is_in_edition_state() and not sp.project.is_busy()


def nodes():
    def walk(items, location):
        for index, node in enumerate(items):
            key = location + [index, node.get_name()]
            yield node, key
            if isinstance(node, sp.layerstack.GroupLayerNode):
                yield from walk(node.sub_layers(), key + ["children"])
            if isinstance(node, sp.layerstack.LayerNode):
                yield from walk(node.content_effects(), key + ["content"])
                if node.has_mask():
                    yield from walk(node.mask_effects(), key + ["mask"])
    for texture_set in sp.textureset.all_texture_sets():
        if compatibility.texture_set_name(texture_set) == "Glass":
            continue
        for stack in texture_set.all_stacks():
            yield from walk(sp.layerstack.get_root_layer_nodes(stack), [compatibility.texture_set_name(texture_set), stack.name()])


def snapshot(customize=True):
    result = {"project": project_path(), "targets": []}
    if not customize or not compatibility.current().customization:
        result['mode'] = 'export_only'
        return result
    for node, location in nodes():
        name = node.get_name()
        if name not in ("PLAYER_NAME", "PLAYER_COLOR1", "PLAYER_COLOR2", "PLAYER_COLOR3"):
            continue
        # Anchor points commonly inherit their parent layer's name. Only color
        # layers are targets; never mistake an identically named anchor for one.
        if name.startswith("PLAYER_COLOR") and not isinstance(node, sp.layerstack.LayerNode):
            continue
        entry = {"location": location, "name": name, "uid": node.uid()}
        if name == "PLAYER_NAME":
            if not isinstance(node, sp.layerstack.FillEffectNode) or not node.is_in_mask_stack():
                raise ValueError(f"{location}: PLAYER_NAME must be a mask Fill using a Font resource.")
            source = node.get_source()
            if not isinstance(source, sp.source.SourceFont):
                raise ValueError(f"{location}: PLAYER_NAME does not use a Font.")
            entry.update(kind="font", text=source.get_parameters().text,
                         resource=source.resource_id.url())
        else:
            if not isinstance(node, sp.layerstack.FillLayerNode):
                raise ValueError(f"{location}: the color must be in a Fill Layer.")
            source = node.get_source(sp.textureset.ChannelType.BaseColor)
            if not isinstance(source, sp.source.SourceUniformColor):
                raise ValueError(f"{location}: Base Color must be an independent uniform color, not a material.")
            color = source.get_color()
            space = color.color_space
            entry.update(kind="color", index=int(name[-1]) - 1, value=list(color.value_raw),
                         space={"enum": space.name} if isinstance(space, sp.colormanagement.GenericColorSpace) else {"string": space})
        result["targets"].append(entry)
    return result


def resolve_targets(saved):
    if project_path().casefold() != saved["project"].casefold():
        raise ValueError("The open project differs from the recovery record project.")
    current = {tuple(location): node for node, location in nodes()}
    resolved = []
    for target in saved["targets"]:
        node = current.get(tuple(target["location"]))
        if node is None or node.get_name() != target["name"]:
            raise ValueError("The layer structure changed. Automatic restoration is unsafe: " + str(target["location"]))
        source = node.get_source(None if target["kind"] == "font" else sp.textureset.ChannelType.BaseColor)
        if target["kind"] == "font":
            if not isinstance(source, sp.source.SourceFont) or source.resource_id.url() != target["resource"]:
                raise ValueError("The Font resource changed after the batch started.")
        elif not isinstance(source, sp.source.SourceUniformColor):
            raise ValueError("Base Color is no longer a uniform color.")
        resolved.append((target, source))
    return resolved


def original_color(target):
    space = target["space"]
    color_space = sp.colormanagement.GenericColorSpace[space["enum"]] if "enum" in space else space["string"]
    return sp.colormanagement.Color(*target["value"], color_space=color_space)


def filename_color_defaults(saved):
    """Only a single original color (at TM palette precision) can name all texture sets."""
    colors = [{}, {}]
    for target in saved["targets"]:
        index = target.get("index")
        if target.get("kind") != "color" or index not in (0, 1):
            continue
        rgb = original_color(target).value
        value = "#" + "".join(format(max(0, min(255, round(channel * 255))), "02X") for channel in rgb)
        colors[index][tm_text.from_hex6(value)] = value
    return [next(iter(values.values())) if len(values) == 1 else None for values in colors]


def apply(saved, row=None):
    if not saved['targets']:
        if project_path().casefold() != saved['project'].casefold():
            raise ValueError('The open project changed during export.')
        return
    if not compatibility.current().customization:
        raise ValueError('Restoring or applying customization requires Painter 10.0.0 or later.')
    resolved = resolve_targets(saved)  # Validate the whole structure before the first edit.
    with sp.layerstack.ScopedModification("CREAM: restore" if row is None else "CREAM: " + row["name"]):
        for target, source in resolved:
            if target["kind"] == "font":
                params = source.get_parameters()
                params.text = target["text"] if row is None else row["name"]
                source.set_parameters(params)
            else:
                hex_color = row["colors"][target["index"]] if row else None
                if hex_color:
                    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
                    color = sp.colormanagement.Color(*rgb, color_space=sp.colormanagement.GenericColorSpace.sRGB)
                else:
                    color = original_color(target)
                source.set_color(color)


def preset_maps():
    if not hasattr(sp.export, 'list_resource_export_presets'):
        # Painter 9 can use an installed preset by URL, but cannot introspect it.
        # Preserve its actual channel packing; do not guess the user's map inputs.
        import substance_painter.resource as resource
        matches = [r for r in resource.search('TM2020')
                   if r.identifier().name == 'TM2020' and r.type() == resource.Type.EXPORT]
        if len(matches) != 1:
            raise ValueError('Exactly one export preset named TM2020 is required in the Painter libraries.')
        return {'legacy_preset': matches[0].identifier().url()}
    matches = [p for p in sp.export.list_resource_export_presets() if p.resource_id.name == "TM2020"]
    if len(matches) != 1:
        raise ValueError("Exactly one export preset named TM2020 is required in the Painter libraries.")
    return matches[0].list_output_maps()


def export_config(maps, texture_set, suffix, size, directory):
    template = "$textureSet_" + suffix
    legacy = isinstance(maps, dict) and 'legacy_preset' in maps
    # The old preset may contain DirectX normals. Override that one map with
    # an explicit OpenGL virtual map; all other maps retain the installed preset.
    if legacy and suffix == 'N':
        maps = [{'fileName': template, 'channels': [
            {'destChannel': c, 'srcChannel': c, 'srcMapType': 'virtualMap',
             'srcMapName': 'Normal_OpenGL'} for c in 'RGB']}]
        legacy = False
    matched = [] if legacy else [m for m in maps if m["fileName"] == template]
    if not legacy and len(matched) != 1:
        raise ValueError(f"The TM2020 preset does not contain exactly one output {template}.")
    output = {} if legacy else copy.deepcopy(matched[0])
    output["fileName"] = texture_set + "_" + suffix
    if suffix == "N":
        # Ask Painter for the target convention at export time. Never flip
        # pixels after export, including when TM2020 is already OpenGL.
        for channel in output.get("channels", []):
            if (channel.get("srcMapType") == "virtualMap"
                    and channel.get("srcMapName") == "Normal_DirectX"):
                channel["srcMapName"] = "Normal_OpenGL"
        rgb = [c for c in output.get("channels", []) if c.get("destChannel") in ("R", "G", "B")]
        if ({c.get("destChannel") for c in rgb} != {"R", "G", "B"}
                or any(c.get("srcMapType") != "virtualMap" or c.get("srcMapName") != "Normal_OpenGL" for c in rgb)):
            raise ValueError("Configure the TM2020 preset _N output with RGB from Converted maps → Normal OpenGL.")
    width, height = dimensions(texture_set, size)
    # ResourceExportPreset.list_output_maps() supplies map definitions, but
    # does not guarantee the export dialog's padding setting. Inline presets
    # must resolve it explicitly, including during list_project_textures().
    params = {"fileFormat": "png", "bitDepth": "8", "dithering": False,
              "paddingAlgorithm": "infinite",
              "sizeLog2": [width.bit_length() - 1, height.bit_length() - 1]}
    if legacy:
        return {'exportPath': str(directory), 'exportShaderParams': False,
                'defaultExportPreset': maps['legacy_preset'],
                'exportList': [{'rootPath': texture_set, 'filter': {'outputMaps': [template]}}],
                'exportParameters': [{'parameters': params}]}
    output.setdefault("parameters", {}).update(params)
    return {"exportPath": str(directory), "exportShaderParams": False,
            "defaultExportPreset": "CREAM_single", "exportPresets": [{"name": "CREAM_single", "maps": [output]}],
            "exportList": [{"rootPath": texture_set}], "exportParameters": [{"parameters": params}]}


def preflight_exports(maps, selections, directory):
    actual_sets = {compatibility.texture_set_name(s): s for s in sp.textureset.all_texture_sets()}
    for item in selections:
        name = item["set"]
        if name not in actual_sets:
            raise ValueError(f"Missing texture set: {name}")
        stacks = actual_sets[name].all_stacks()
        if len(stacks) != 1 or stacks[0].name():
            raise ValueError("This version of CREAM does not support material layering: " + name)
        config = export_config(maps, name, item["map"], item["size"], directory)
        files = [p for values in sp.export.list_project_textures(config).values() for p in values]
        if len(files) != 1 or Path(files[0]).name != f"{name}_{item['map']}.png":
            raise ValueError(f"Unexpected outputs in {name}_{item['map']} (UDIM is not supported): {files}")


def export_one(maps, selection, directory):
    config = export_config(maps, selection["set"], selection["map"], selection["size"], directory)
    result = sp.export.export_project_textures(config)
    if result.status != sp.export.ExportStatus.Success:
        raise RuntimeError(f"Export did not complete: {result.status.name}: {result.message}")
    files = [Path(p) for values in result.textures.values() for p in values]
    expected = Path(directory) / f"{selection['set']}_{selection['map']}.png"
    if len(files) != 1 or files[0].resolve() != expected.resolve() or not expected.is_file():
        raise RuntimeError("Painter did not generate exactly the expected texture.")
    return expected
