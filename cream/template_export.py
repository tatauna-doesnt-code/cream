"""Read installed templates and predict outputs; never edit the user's template."""
import copy
from pathlib import Path
import substance_painter as sp
from . import compatibility, core


def legacy_library_templates():
    """General resource search omits .spexp files on some older Painter hosts."""
    resource = sp.resource
    if not hasattr(resource, 'Shelves'):
        return []
    found = []
    for shelf in resource.Shelves.all():
        try:
            root = Path(shelf.path())
            # Limit filesystem discovery to registered libraries and their preset
            # directory. Resolve through Painter's resource URL, never import files.
            paths = list(root.glob('*.spexp'))
            paths += list((root / 'export-presets').rglob('*.spexp'))
            for path in paths:
                if path.is_file():
                    identifier = resource.ResourceID(context=shelf.name(), name=path.stem)
                    found.append({'name': identifier.name, 'url': identifier.url(), 'kind': 'legacy'})
        except OSError:
            # A disconnected library must not hide presets from accessible ones.
            # The diagnostic report records folder accessibility independently.
            continue
    return found


def templates():
    found = []
    if hasattr(sp.export, 'list_resource_export_presets'):
        for preset in sp.export.list_resource_export_presets():
            found.append({'name': preset.resource_id.name, 'url': preset.resource_id.url(), 'kind': 'resource'})
        for preset in sp.export.list_predefined_export_presets():
            found.append({'name': preset.name, 'url': preset.url, 'kind': 'predefined'})
    else:
        import substance_painter.resource
        for resource in sp.resource.search(''):
            # Older SDK enums can lag behind installed library resource types
            # (for example 'vectorial'). One unrelated asset must not abort discovery.
            try:
                resource_type = resource.type()
            except ValueError:
                continue
            if resource_type == sp.resource.Type.EXPORT:
                identifier = resource.identifier()
                found.append({'name': identifier.name, 'url': identifier.url(), 'kind': 'legacy'})
        found.extend(legacy_library_templates())
    # Versioned resource-search URLs and unversioned library URLs can identify
    # the same preset. Prefer the resource-search entry when available.
    unique = {}
    for item in found:
        unique.setdefault(item['url'].split('?version=', 1)[0], item)
    return sorted(unique.values(), key=lambda item: (item['name'].casefold(), item['url']))


def texture_sets():
    return list(sp.textureset.all_texture_sets())


def parameters(name, size):
    width, height = core.dimensions(name, size)
    return {'fileFormat': 'png', 'bitDepth': '8', 'dithering': False,
            'paddingAlgorithm': 'infinite', 'sizeLog2': [width.bit_length()-1, height.bit_length()-1]}


def config(template, name, directory, size=1024, definition=None):
    result = {'exportPath': str(directory), 'exportShaderParams': False,
              'defaultExportPreset': template['url'], 'exportList': [{'rootPath': name}],
              'exportParameters': [{'parameters': parameters(name, size)}]}
    if definition is not None:
        output = copy.deepcopy(definition)
        output['fileName'] = 'cream_output'
        output.setdefault('parameters', {}).update(parameters(name, size))
        result.update(defaultExportPreset='CREAM_output', exportPresets=[{'name': 'CREAM_output', 'maps': [output]}])
    return result


def files_for(config):
    return [Path(path) for paths in sp.export.list_project_textures(config).values() for path in paths]


def definitions(template, stack):
    if template['kind'] == 'legacy':
        return None
    if template['kind'] == 'resource':
        presets = sp.export.list_resource_export_presets()
        matches = [p for p in presets if p.resource_id.url() == template['url']]
        return matches[0].list_output_maps() if len(matches) == 1 else None
    presets = sp.export.list_predefined_export_presets()
    matches = [p for p in presets if p.url == template['url']]
    return matches[0].list_output_maps(stack) if len(matches) == 1 else None


def discover(template, directory):
    """Obtain actual filenames, including template substitutions, without rendering."""
    result = {}
    for texture_set in texture_sets():
        name = compatibility.texture_set_name(texture_set)
        stacks = texture_set.all_stacks()
        if len(stacks) != 1 or stacks[0].name():
            raise ValueError('Material layering is not supported: ' + name)
        if hasattr(texture_set, 'has_uv_tiles') and texture_set.has_uv_tiles():
            raise ValueError('UV-tile / UDIM projects are not supported: ' + name)
        maps = definitions(template, stacks[0])
        records = []
        if maps is None:
            outputs = [(path, None, path.name) for path in files_for(config(template, name, directory))]
        else:
            outputs = []
            for definition in maps:
                # Probe one definition with the original filename. Export later uses a safe temporary name.
                probe = config(template, name, directory)
                probe_map = copy.deepcopy(definition)
                probe_map.setdefault('parameters', {}).update(parameters(name, 1024))
                probe.update(defaultExportPreset='CREAM_probe', exportPresets=[{'name': 'CREAM_probe', 'maps': [probe_map]}])
                paths = files_for(probe)
                if len(paths) != 1:
                    raise ValueError('Each template output must produce one texture per set (no UDIM): ' + name)
                outputs.append((paths[0], definition, definition['fileName']))
        seen = set()
        for path, definition, identity in outputs:
            if path.parent.resolve() != Path(directory).resolve() or path.suffix.lower() != '.png':
                raise ValueError('Template outputs must be flat PNG filenames without subfolders: ' + str(path))
            if path.name.casefold() in seen:
                raise ValueError('The template produces duplicate filenames in ' + name)
            seen.add(path.name.casefold())
            prefix, separator, suffix = path.stem.rpartition('_')
            if path.stem.startswith(name + '_'):
                prefix, separator, suffix = name, '_', path.stem[len(name) + 1:]
            if not separator:
                prefix, suffix = '', path.stem
            records.append({'id': identity, 'source': path.name, 'definition': definition, 'separator': bool(separator),
                            'prefix': prefix, 'suffix': suffix,
                            'compression': core.MAPS.get(suffix, 'BC3_UNORM').split('_')[0]})
        result[name] = records
    return result


def output_filename(selection):
    suffix = selection['suffix']
    if not suffix or len(suffix) > 100 or suffix != core.safe_stem(suffix) or '.' in suffix:
        raise ValueError('Use a nonempty texture suffix without dots, path separators or reserved filename characters.')
    prefix = selection.get('prefix', '')
    filename = prefix + ('_' if prefix or selection.get('separator') else '') + suffix + '.dds'
    if filename[:-4] != core.safe_stem(filename[:-4]):
        raise ValueError('The template output filename is unsafe: ' + filename)
    return filename


def preflight(plan, selections, directory):
    actual = discover(plan['template'], directory)
    stacks = {compatibility.texture_set_name(item): item.all_stacks()[0] for item in texture_sets()}
    channel_type = getattr(sp.textureset, 'ChannelType', None)
    channel_types = {name.casefold(): value for name, value in getattr(channel_type, '__members__', {}).items()}
    occupied = set()
    for selection in selections:
        name = selection['set']
        record = next((r for r in actual.get(name, []) if r['id'] == selection['map']), None)
        if record is None or any(record.get(k) != selection.get(k) for k in ('source', 'prefix', 'separator', 'definition')):
            raise ValueError('The project or export template changed. Refresh the Textures tab and review your selections.')
        filename = output_filename(selection)
        stack = stacks[name]
        missing = set()
        if hasattr(stack, 'has_channel'):
            for source in (record['definition'] or {}).get('channels', []):
                if source.get('srcMapType') != 'documentMap':
                    continue
                source_name = source.get('srcMapName', '')
                source_type = channel_types.get(source_name.casefold())
                if source_type is not None and not stack.has_channel(source_type):
                    missing.add(source_name)
        if missing:
            channels = ', '.join(sorted(missing, key=str.casefold))
            raise ValueError(f'{filename}: the export template needs {channels} in texture set "{name}". '
                             'Add the required channel in Painter, use a compatible template, '
                             'or deselect this output in CREAM.')
        if filename.casefold() in occupied:
            raise ValueError('Two selected outputs have the same ZIP filename: ' + filename)
        occupied.add(filename.casefold())
        core.dds_format(selection['compression'])


def painter_export_error(selection, detail):
    if 'see logs' in detail.casefold():
        detail = 'Open Substance 3D Painter’s Log panel and look for the MapExporter error.'
    return RuntimeError(f'Painter could not export {selection["source"]} from texture set '
                        f'"{selection["set"]}": {detail}')


def export_one(plan, selection, directory):
    # Isolate every operation: legacy hosts export the entire template for this set/resolution.
    import tempfile
    target = Path(tempfile.mkdtemp(prefix='map-', dir=directory))
    definition = selection.get('definition')
    export = config(plan['template'], selection['set'], target, selection['size'], definition)
    expected = target / ('cream_output.png' if definition is not None else selection['source'])
    try:
        result = sp.export.export_project_textures(export)
    except RuntimeError as exc:
        raise painter_export_error(selection, str(exc)) from exc
    if result.status != sp.export.ExportStatus.Success:
        raise painter_export_error(selection, str(getattr(result, 'message', '') or result.status))
    paths = [Path(p).resolve() for items in result.textures.values() for p in items]
    if expected.resolve() not in paths or not expected.is_file():
        raise RuntimeError('Painter did not produce the selected template output: ' + expected.name)
    return expected
