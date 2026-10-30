"""Painter 12.1 adapter. Every function in this module runs on the UI thread."""
import copy
from pathlib import Path

import substance_painter as sp
import substance_painter.colormanagement
import substance_painter.export
import substance_painter.layerstack
import substance_painter.project
import substance_painter.source
import substance_painter.textureset

from .core import dimensions


def project_path():
    if not sp.project.is_open() or not sp.project.file_path():
        raise ValueError("Abra um projeto .spp salvo antes de continuar.")
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
        if texture_set.name == "Glass":
            continue
        for stack in texture_set.all_stacks():
            yield from walk(sp.layerstack.get_root_layer_nodes(stack), [str(texture_set.name), stack.name()])


def snapshot():
    result = {"project": project_path(), "targets": []}
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
                raise ValueError(f"{location}: PLAYER_NAME deve ser um Fill na máscara com recurso Font.")
            source = node.get_source()
            if not isinstance(source, sp.source.SourceFont):
                raise ValueError(f"{location}: PLAYER_NAME não usa Font.")
            entry.update(kind="font", text=source.get_parameters().text,
                         resource=source.resource_id.url())
        else:
            if not isinstance(node, sp.layerstack.FillLayerNode):
                raise ValueError(f"{location}: a cor precisa estar em um Fill Layer.")
            source = node.get_source(sp.textureset.ChannelType.BaseColor)
            if not isinstance(source, sp.source.SourceUniformColor):
                raise ValueError(f"{location}: Base Color precisa ser uma cor sólida independente (não um material).")
            color = source.get_color()
            space = color.color_space
            entry.update(kind="color", index=int(name[-1]) - 1, value=list(color.value_raw),
                         space={"enum": space.name} if isinstance(space, sp.colormanagement.GenericColorSpace) else {"string": space})
        result["targets"].append(entry)
    if not any(t["kind"] == "font" for t in result["targets"]):
        raise ValueError("Nenhum PLAYER_NAME com Font encontrado nas máscaras fora de Glass.")
    return result


def resolve_targets(saved):
    if project_path().casefold() != saved["project"].casefold():
        raise ValueError("O projeto aberto é diferente do projeto do registro de recuperação.")
    current = {tuple(location): node for node, location in nodes()}
    resolved = []
    for target in saved["targets"]:
        node = current.get(tuple(target["location"]))
        if node is None or node.get_name() != target["name"]:
            raise ValueError("A estrutura de layers mudou. Não é seguro restaurar automaticamente: " + str(target["location"]))
        source = node.get_source(None if target["kind"] == "font" else sp.textureset.ChannelType.BaseColor)
        if target["kind"] == "font":
            if not isinstance(source, sp.source.SourceFont) or source.resource_id.url() != target["resource"]:
                raise ValueError("O recurso Font mudou desde o início do lote.")
        elif not isinstance(source, sp.source.SourceUniformColor):
            raise ValueError("O Base Color deixou de ser uma cor sólida.")
        resolved.append((target, source))
    return resolved


def original_color(target):
    space = target["space"]
    color_space = sp.colormanagement.GenericColorSpace[space["enum"]] if "enum" in space else space["string"]
    return sp.colormanagement.Color(*target["value"], color_space=color_space)


def apply(saved, row=None):
    resolved = resolve_targets(saved)  # Validate the whole structure before the first edit.
    with sp.layerstack.ScopedModification("KR7: restaurar" if row is None else "KR7: " + row["name"]):
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
    matches = [p for p in sp.export.list_resource_export_presets() if p.resource_id.name == "TM2020"]
    if len(matches) != 1:
        raise ValueError("É necessário exatamente um preset de exportação chamado TM2020 nas bibliotecas do Painter.")
    return matches[0].list_output_maps()


def export_config(maps, texture_set, suffix, size, directory):
    template = "$textureSet_" + suffix
    matched = [m for m in maps if m["fileName"] == template]
    if len(matched) != 1:
        raise ValueError(f"O preset TM2020 não contém uma única saída {template}.")
    output = copy.deepcopy(matched[0])
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
            raise ValueError("Configure a saída _N do preset TM2020 com RGB de Converted maps → Normal OpenGL.")
    width, height = dimensions(texture_set, size)
    # ResourceExportPreset.list_output_maps() supplies map definitions, but
    # does not guarantee the export dialog's padding setting. Inline presets
    # must resolve it explicitly, including during list_project_textures().
    params = {"fileFormat": "png", "bitDepth": "8", "dithering": False,
              "paddingAlgorithm": "infinite",
              "sizeLog2": [width.bit_length() - 1, height.bit_length() - 1]}
    output.setdefault("parameters", {}).update(params)
    return {"exportPath": str(directory), "exportShaderParams": False,
            "defaultExportPreset": "KR7_single", "exportPresets": [{"name": "KR7_single", "maps": [output]}],
            "exportList": [{"rootPath": texture_set}], "exportParameters": [{"parameters": params}]}


def preflight_exports(maps, selections, directory):
    actual_sets = {str(s.name): s for s in sp.textureset.all_texture_sets()}
    for item in selections:
        name = item["set"]
        if name not in actual_sets:
            raise ValueError(f"Texture set ausente: {name}")
        stacks = actual_sets[name].all_stacks()
        if len(stacks) != 1 or stacks[0].name():
            raise ValueError("Esta versão do KR7 não suporta material layering: " + name)
        config = export_config(maps, name, item["map"], item["size"], directory)
        files = [p for values in sp.export.list_project_textures(config).values() for p in values]
        if len(files) != 1 or Path(files[0]).name != f"{name}_{item['map']}.png":
            raise ValueError(f"Saídas inesperadas em {name}_{item['map']} (UDIM não é suportado): {files}")


def export_one(maps, selection, directory):
    config = export_config(maps, selection["set"], selection["map"], selection["size"], directory)
    result = sp.export.export_project_textures(config)
    if result.status != sp.export.ExportStatus.Success:
        raise RuntimeError(f"Export não concluído: {result.status.name}: {result.message}")
    files = [Path(p) for values in result.textures.values() for p in values]
    expected = Path(directory) / f"{selection['set']}_{selection['map']}.png"
    if len(files) != 1 or files[0].resolve() != expected.resolve() or not expected.is_file():
        raise RuntimeError("O Painter não gerou exatamente a textura esperada.")
    return expected
