"""Real Qt + DDS/ZIP checks with simulated Painter APIs, including pre-8.3 startup."""
import copy
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import types
from unittest.mock import patch
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
version = tuple(map(int, (sys.argv[1] if len(sys.argv)>1 else '12.1.3').split('.')))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
if version >= (10, 1, 0):
    dll = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
    from PySide6 import QtCore, QtGui, QtWidgets as W
else:
    from PySide2 import QtCore, QtGui, QtWidgets as W

class QtTest:
    class QTest:
        @staticmethod
        def mouseClick(widget, button, modifiers, position):
            for kind in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease):
                event = QtGui.QMouseEvent(kind, QtCore.QPointF(position), button,
                    button if kind == QtCore.QEvent.MouseButtonPress else QtCore.Qt.NoButton, modifiers)
                W.QApplication.sendEvent(widget, event)

        @staticmethod
        def keyClick(widget, key):
            for kind in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
                W.QApplication.sendEvent(widget, QtGui.QKeyEvent(kind, key, QtCore.Qt.NoModifier))
app = W.QApplication.instance() or W.QApplication([])
app.setApplicationVersion('.'.join(map(str, version)))
app.setStyle('Fusion')
palette = QtGui.QPalette()
for role, value in [('Window','#303030'),('WindowText','#eeeeee'),('Base','#222426'),('Text','#eeeeee'),('Button','#393939'),('ButtonText','#eeeeee'),('Highlight','#365568'),('HighlightedText','#ffffff')]:
    palette.setColor(getattr(QtGui.QPalette, role), QtGui.QColor(value))
app.setPalette(palette)
sp = types.ModuleType('substance_painter')
sp.__path__ = []
sys.modules['substance_painter'] = sp
modules = ['ui','project','textureset','export','resource']
if version >= (8,3,0): modules += ['application']
if version >= (10,0,0): modules += ['layerstack','source','colormanagement']
for name in modules:
    module = types.ModuleType('substance_painter.'+name)
    setattr(sp, name, module)
    sys.modules[module.__name__] = module
if 'application' in modules: sp.application.version_info = lambda: version
sp.ui.get_main_window = lambda: None
sp.ui.ApplicationMenu = types.SimpleNamespace(Window=1)
sp.ui.add_action = lambda *args: None
toolbar_launchers = []
sp.ui.add_plugins_toolbar_widget = toolbar_launchers.append
sp.ui.delete_ui_element = lambda obj: obj.deleteLater()
project_open = False
sp.project.is_open = lambda: project_open
sp.project.is_busy = lambda: False
sp.project.is_in_edition_state = lambda: True
class PropertyName(str):
    def __call__(self):
        raise AssertionError('Deprecated name() compatibility wrapper must not be called')
sets = ['Body','Tyres']
stack = types.SimpleNamespace(name=lambda: '')
sp.textureset.all_texture_sets = lambda: [types.SimpleNamespace(name=PropertyName(name) if version >= (11,0,0) else lambda n=name:n,
                                                              all_stacks=lambda:[stack]) for name in sets]
if version >= (10,0,0): sp.layerstack.get_root_layer_nodes = lambda s: []
maps = [{'fileName':'$textureSet_B','channels':[{'destChannel':'R','srcChannel':'G','srcMapType':'documentMap','srcMapName':'baseColor'}]},
        {'fileName':'$textureSet_R','channels':[]},
        {'fileName':'$textureSet_N','channels':[{'destChannel':c,'srcChannel':c,'srcMapType':'virtualMap','srcMapName':'Normal_DirectX'} for c in 'RGB']}]
catalog = [{'name':'TM2020','url':'resource://test/TM2020'}, {'name':'Other','url':'resource://test/Other'}]
class Preset:
    def __init__(self, name, url):
        self.resource_id = types.SimpleNamespace(name=name,url=lambda:url)
    def list_output_maps(self): return copy.deepcopy(maps)
sp.resource.Type = types.SimpleNamespace(EXPORT=1)
def unknown_resource_type():
    raise ValueError("'vectorial' is not a valid Type")
sp.resource.search = lambda q: [types.SimpleNamespace(type=unknown_resource_type)] + [types.SimpleNamespace(identifier=lambda p=p:types.SimpleNamespace(name=p['name'],url=lambda:p['url']), type=lambda:1) for p in catalog]
library_fixture = tempfile.TemporaryDirectory(prefix='cream-library-')
library_root = Path(library_fixture.name)
(library_root / 'export-presets').mkdir()
def library_shelves():
    directory = library_root / 'export-presets'
    for path in directory.glob('*.spexp'):
        path.unlink()
    for item in catalog:
        (directory / (item['name'] + '.spexp')).write_bytes(b'fixture')
    return [types.SimpleNamespace(name=lambda: 'test', path=lambda: str(library_root), is_crawling=lambda: False)]
sp.resource.Shelves = types.SimpleNamespace(all=library_shelves)
sp.resource.ResourceID = lambda context, name: types.SimpleNamespace(name=name, url=lambda: 'resource://' + context + '/' + name)
if version < (10,0,0):
    # Real 9.1.2 diagnostics: resource search omits every export preset.
    sp.resource.search = lambda q: [types.SimpleNamespace(type=unknown_resource_type)]
if version >= (10,0,0):
    sp.export.list_resource_export_presets = lambda:[Preset(**p) for p in catalog]
    sp.export.list_predefined_export_presets = lambda:[]

def paths(config):
    name = config['exportList'][0]['rootPath']
    definitions = config['exportPresets'][0]['maps'] if 'exportPresets' in config else maps
    return {(name,''):[str(Path(config['exportPath'])/(m['fileName'].replace('$textureSet',name)+'.png')) for m in definitions]}

def png(path,w,h):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))
    Path(path).write_bytes(data+chunk(b'IDAT',zlib.compress((b'\0'+b'\xa0\xb0\xc0'*w)*h))+chunk(b'IEND',b''))

exports=[]
def export(config):
    exports.append(copy.deepcopy(config))
    size=config['exportParameters'][0]['parameters']['sizeLog2']
    output=paths(config)
    for filename in next(iter(output.values())): png(filename,2**size[0],2**size[1])
    return types.SimpleNamespace(status='success',textures=output)
sp.export.list_project_textures=paths
sp.export.export_project_textures=export
sp.export.ExportStatus=types.SimpleNamespace(Success='success')
from cream import ui, bootstrap, template_export, compatibility, core, painter

with tempfile.TemporaryDirectory() as folder, patch.object(ui,'DATA',Path(folder)), patch.object(bootstrap,'DATA',Path(folder)):
    if version >= (10, 0, 0):
        from enum import Enum
        channel_type = Enum('ChannelType', ['BaseColor', 'Specular'])
        plan = {'template': template_export.templates()[-1]}
        with patch.object(sp.textureset, 'ChannelType', channel_type, create=True), \
             patch.object(stack, 'has_channel', lambda channel: channel != channel_type.Specular, create=True), \
             patch.dict(maps[0]['channels'][0], srcMapName='specular'):
            record = template_export.discover(plan['template'], folder)['Body'][0]
            selection = dict(record, set='Body', map=record['id'], size=1024)
            try:
                template_export.preflight(plan, [selection], folder)
            except ValueError as exc:
                assert 'Body_B.dds' in str(exc) and 'needs specular' in str(exc)
            else:
                raise AssertionError('Missing Specular was not caught before export')
        with patch.object(sp.export, 'export_project_textures', side_effect=RuntimeError('Error during the export (see logs).')):
            try:
                template_export.export_one(plan, selection, folder)
            except RuntimeError as exc:
                assert 'Body_B.png' in str(exc) and 'MapExporter' in str(exc)
            else:
                raise AssertionError('Expected a contextual Painter export error')
    sp.project.file_path=lambda:str(Path(folder)/'skin.spp')
    window=ui.Window(auto_update=False)
    window.show()
    app.processEvents()
    assert not window.project_required_notice.isHidden()
    assert window.tabs.currentWidget() == window.settings_page
    for page in (window.textures_page, window.naming_page, window.skins_page, window.log_page):
        assert not window.tabs.isTabEnabled(window.tabs.indexOf(page))
        assert not page.isEnabled()
    assert window.settings_page.isEnabled() and window.help_page.isEnabled()
    assert not window.export_button.isEnabled() and not window.validate_button.isEnabled()
    assert not hasattr(window, "diagnostics_button")
    assert window.texture_sets.template.count() == 3
    project_open = True
    window.texture_sets.reload()
    window.refresh_project_gate()
    assert window.project_required_notice.isHidden()
    assert all(window.tabs.isTabEnabled(i) for i in range(window.tabs.count()))
    window.tabs.setCurrentWidget(window.textures_page)
    texture=window.texture_sets
    # Path fields and their Browse buttons share one 32px-high row, including
    # after Qt polishes the stylesheet. The diagnostic input follows the same rule.
    for key, page in [('output', window.settings_page), ('base', window.skins_page)]:
        window.tabs.setCurrentWidget(page)
        app.processEvents()
        field = window.fields[key]
        browse = field.parentWidget().findChild(W.QPushButton)
        assert field.height() == browse.height() == 32, (key, field.height(), browse.height())
        assert field.mapToGlobal(QtCore.QPoint()).y() == browse.mapToGlobal(QtCore.QPoint()).y()
    window.tabs.setCurrentWidget(window.settings_page)
    app.processEvents()
    window.grab().save(str(ROOT/'dist'/('settings-local-'+'.'.join(map(str,version))+'.png')))
    window.tabs.setCurrentWidget(window.help_page)
    app.processEvents()
    faq_toggles = [b for b in window.help_page.findChildren(W.QToolButton) if b.isCheckable()]
    assert faq_toggles
    for toggle in faq_toggles:
        assert toggle.arrowType() == QtCore.Qt.NoArrow
        assert toggle.iconSize() == QtCore.QSize(8, 8)
    faq_toggles[0].click()
    assert faq_toggles[0].iconSize() == next(iter(texture.groups.values())).expand.iconSize()
    window.grab().save(str(ROOT/'dist'/('help-local-'+'.'.join(map(str,version))+'.png')))
    faq_toggles[0].click()
    window.tabs.setCurrentWidget(window.textures_page)
    with patch.object(W.QMessageBox, 'warning') as warning:
        window.show_compatibility_warning()
        window.show_compatibility_warning()
        assert warning.call_count == (1 if version < (10, 1, 2) else 0)
    assert window.compatibility_notice.isHidden() == (version >= (10, 1, 2))
    assert window.recover_button.isEnabled() == (version >= (10, 0, 0))
    assert compatibility.current().version == version
    assert compatibility.current().export
    assert set(texture.groups)==set(sets), texture.problem
    assert 'Wheels' not in texture.groups
    assert not texture.problem
    assert texture.selected_template()['name']=='TM2020'
    tab_index = window.tabs.indexOf(window.textures_page)
    assert window.tabs.tabText(tab_index) == '1 TEXTURES'
    assert window.tabs.tabBar().tabButton(tab_index, W.QTabBar.LeftSide) is None
    plain_tab_width = window.tabs.tabBar().tabRect(tab_index).width()
    assert window.capabilities.customization==(version >= (10,0,0))
    window.fields['output'].setText(folder)
    group=texture.groups['Body']
    group.set_expanded(True)
    suffix, compression=group.suffixes[0],group.compressions[0]
    suffix.input.setText('CoatR')
    with patch.object(W.QMessageBox,'warning',return_value=W.QMessageBox.Cancel) as warning:
        suffix.edited()
        assert suffix.value()=='B' and warning.call_count==1
    suffix.input.setText('CoatR')
    with patch.object(W.QMessageBox,'warning',return_value=W.QMessageBox.Ok) as warning:
        suffix.edited()
        compression.input.setCurrentText('BC4')
        compression.edited()
        assert warning.call_count==1
    assert suffix.input.font().bold() and suffix.input.font().italic()
    assert suffix.reset.isEnabled()
    assert '*' in window.tabs.tabText(window.tabs.indexOf(window.textures_page)) and window.tabs.tabBar().modified_index == window.tabs.indexOf(window.textures_page)
    assert not compression.alert.toolTip()
    compression.input.setCurrentText('BC1');compression.edited()
    assert compression.alert.toolTip() and not window.tabs.tabIcon(window.tabs.indexOf(window.textures_page)).isNull()
    app.processEvents()
    warning_tab_width = window.tabs.tabBar().tabRect(tab_index).width()
    assert warning_tab_width > plain_tab_width
    bar = window.tabs.tabBar()
    point = QtCore.QPointF(bar.tabRect(window.tabs.indexOf(window.textures_page)).center())
    event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, point, QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
    bar.mouseMoveEvent(event)
    assert W.QToolTip.text() == window.tabs.tabToolTip(window.tabs.indexOf(window.textures_page))
    W.QToolTip.hideText()
    compression.input.setCurrentText('BC4');compression.edited()
    group.table.item(0,0).setCheckState(QtCore.Qt.Checked)
    group.sizes[0].setCurrentIndex(group.sizes[0].findData(1024))
    assert window.export_button.isEnabled()
    saved=texture.settings()
    window.save_settings()
    texture.reload(force=True)
    assert texture.settings()==saved
    assert texture.groups['Body'].suffixes[0].input.font().bold()
    def finish():
        deadline=time.monotonic()+40
        while window.runner is not None and time.monotonic()<deadline:
            app.processEvents();time.sleep(.01)
        assert window.runner is None
        assert window.report['status']=='completed',window.report
    window.start();finish()
    with zipfile.ZipFile(window.report['rows'][0]['output']) as archive:
        assert archive.namelist()==['Body_CoatR.dds']
        assert archive.read('Body_CoatR.dds')[84:88]==b'BC4U'
    if version < (10,0,0):
        assert 'exportPresets' not in exports[0]
        assert len(paths(exports[0])[('Body','')])==3
    else:
        assert exports[0]['exportPresets'][0]['maps'][0]['channels']==maps[0]['channels']
    # Cancel after PNG export, including the legacy sibling outputs. Publish no extra ZIP.
    before = list(Path(folder).glob('*.zip'))
    window.start()
    window.timer.stop()
    window.tick()
    window.tick()
    window.cancel.set()
    deadline = time.monotonic()+30
    while window.runner is not None and time.monotonic()<deadline:
        window.tick();app.processEvents();time.sleep(.01)
    assert window.runner is None and window.report['status']=='cancelled'
    assert list(Path(folder).glob('*.zip'))==before
    assert not list(Path(folder).glob('cream-*'))
    # Baseline and manual overrides both reset; size alone does not change the override marker.
    texture.groups['Body'].suffixes[0].reset.click()
    texture.groups['Body'].compressions[0].reset.click()
    assert '*' not in window.tabs.tabText(window.tabs.indexOf(window.textures_page))
    app.processEvents()
    assert window.tabs.tabBar().tabRect(tab_index).width() < warning_tab_width
    # Explicit duplicate destinations are blocked, never overwritten in the replacements dict.
    group=texture.groups['Body']
    group.table.item(1,0).setCheckState(QtCore.Qt.Checked)
    group.suffixes[1].set_value('B')
    with patch.object(window,'error') as error:
        window.start()
        assert error.call_count==1 and 'same ZIP filename' in str(error.call_args[0][0])
    group.suffixes[1].reset.click()
    group.table.item(1,0).setCheckState(QtCore.Qt.Unchecked)
    # Batch with unchanged model and arbitrary project set names.
    window.restore_reload_state({'rows':[{'id':'1','line':1,'name':'Player','stem':'Player','colors':[None,None,None]}, {'id':'2','line':2,'name':'Second','stem':'Second','colors':[None,None,None]}],
                                 'loaded_sheet':None,'checked':[True,True],'selected':0,'log':''})
    if window.capabilities.customization:
        window.rows[0]['colors'][1] = '#123456'
        with patch.object(painter, 'available_customization_targets', return_value={'PLAYER_NAME'}):
            window.refresh_batch_setup()
            header = window.backers.horizontalHeader()
            assert set(header.warnings) == {4} and 'PLAYER_COLOR2' in header.warnings[4]
            assert not window.tabs.tabIcon(window.tabs.indexOf(window.skins_page)).isNull()
        window.rows[0]['colors'][1] = None
        recovery = window.recovery_path()
        saved = {'project': painter.project_path(), 'targets': []}
        core.atomic_json(recovery, saved)
        window.saved = saved
        with patch.object(painter, 'apply') as apply, patch.object(window, 'error') as error:
            window.restore()
            apply.assert_called_once_with(saved)
            error.assert_not_called()
        assert window.saved is None and not recovery.exists()
        core.atomic_json(recovery, saved)  # Recovery left on disk after restart.
        window.refresh_recovery_controls()
        assert not window.detach_button.isHidden()
        with patch.object(W.QMessageBox, 'warning', return_value=W.QMessageBox.Cancel):
            window.detach_preview()
        assert recovery.exists()
        with patch.object(W.QMessageBox, 'warning', return_value=W.QMessageBox.Yes), \
             patch.object(painter, 'apply') as apply, patch.object(window, 'error') as error:
            window.detach_preview()
            apply.assert_not_called()
            error.assert_not_called()
        assert not recovery.exists() and len(list(Path(folder).glob('detached-*.json'))) == 1
    window.check_rows(False)
    assert window.export_button.text() == 'Export 0 skins' and not window.export_button.isEnabled()
    window.tabs.setCurrentWidget(window.skins_page)
    app.processEvents()
    rect = window.backers.visualItemRect(window.backers.item(0, 0))
    QtTest.QTest.mouseClick(window.backers.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, rect.center())
    assert window.backers.item(0, 0).checkState() == QtCore.Qt.Checked
    assert window.export_button.text() == 'Export 1 skin' and window.export_button.isEnabled()
    assert window.capture_reload_state()['checked'] == [True, False]
    # Space toggles use the same integer check-state path as mouse clicks.
    window.backers.setCurrentCell(0, 0)
    QtTest.QTest.keyClick(window.backers, QtCore.Qt.Key_Space)
    assert window.backers.item(0, 0).checkState() == QtCore.Qt.Unchecked
    QtTest.QTest.keyClick(window.backers, QtCore.Qt.Key_Space)
    assert window.export_button.isEnabled() and window.export_button.text() == 'Export 1 skin'
    rect = window.backers.visualItemRect(window.backers.item(1, 0))
    QtTest.QTest.mouseClick(window.backers.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, rect.center())
    assert window.export_button.isEnabled() and window.export_button.text() == 'Export 2 skins'
    window.start();finish()
    assert len(window.report['rows']) == 2
    assert window.report['mode']=='batch'  
    # Preserve the template's normal convention instead of applying hidden inversion.
    if version >= (10,0,0):
        selection=dict(group.records[2],set='Body',map=group.records[2]['id'],size=1024)
        with tempfile.TemporaryDirectory() as temp:
            template_export.export_one(texture.export_plan(),selection,temp)
            assert exports[-1]['exportPresets'][0]['maps'][0]['channels']==maps[2]['channels']
    window.tabs.setCurrentWidget(window.textures_page)
    group.set_expanded(True)
    group.suffixes[0].set_value('CoatR')
    app.processEvents()
    assert group.table.columnWidth(0) == group.table.rowHeight(0) == 40
    assert group.expand.geometry().left() < 60
    assert group.summary.geometry().left() < group.resolution.geometry().left()
    inputs = [group.suffixes[0].input, group.suffixes[0].reset, group.compressions[0].input, group.compressions[0].reset, group.sizes[0]]
    tops = [widget.mapTo(group.table.viewport(), QtCore.QPoint(0, 0)).y() for widget in inputs]
    assert max(tops) - min(tops) <= 1, tops
    assert all(widget.height() == 32 for widget in inputs)
    window.grab().save(str(ROOT/'dist'/('template-overrides-'+'.'.join(map(str,version))+'.png')))
    # Missing default is a visible, recoverable state; any installed template can be selected.
    catalog[:]=[catalog[1]]
    texture.template.setCurrentIndex(0)
    texture.pending=None
    texture.loaded_url=None
    texture.reload(force=True)
    assert texture.problem and not window.tabs.tabIcon(window.tabs.indexOf(window.textures_page)).isNull()
    assert not window.export_button.isEnabled()
    texture.template.setCurrentIndex(1);texture.load_outputs()
    assert not texture.problem and set(texture.groups)==set(sets)
    # Detect a new project/set inventory, don't export a stale set.
    sets[:]=['OnlySet']
    texture.reload()
    assert set(texture.groups)=={'OnlySet'}
    texture.reference_toggle.click()
    window.tabs.setCurrentWidget(window.textures_page)
    app.processEvents()
    window.grab().save(str(ROOT/'dist'/('template-workflow-'+'.'.join(map(str,version))+'.png')))
    assert not list(Path(folder).glob('cream-*'))
    assert not list(Path(folder).glob('recover-*.json'))
    # Closing a project locks an already-open window; reopening unlocks it.
    project_open = False
    window.texture_sets.reload()
    window.refresh_project_gate()
    assert not window.textures_page.isEnabled()
    assert not window.project_required_notice.isHidden()
    assert window.settings_page.isEnabled() and window.help_page.isEnabled()
    project_open = True
    window.texture_sets.reload()
    window.refresh_project_gate()
    assert window.textures_page.isEnabled() and window.project_required_notice.isHidden()
    assert not window.texture_sets.problem
    for page, label in [(window.settings_page, 'settings'), (window.skins_page, 'batch'), (window.naming_page, 'naming'), (window.textures_page, 'textures')]:
        window.tabs.setCurrentWidget(page)
        app.processEvents()
        window.grab().save(str(ROOT/'dist'/('pass6-'+label+'-'+'.'.join(map(str,version))+'.png')))
    window.stop_background_tasks()
    window.hide()
    import cream as plugin
    with patch.object(plugin, 'show_window') as launch:
        plugin.start_plugin(apply_update=False)
        launcher = plugin._toolbar_button
        assert launcher is not None and not launcher.icon().isNull()
        assert launcher.toolButtonStyle() == QtCore.Qt.ToolButtonIconOnly
        assert launcher.toolTip() == 'Open CREAM'
        assert len(toolbar_launchers) == 1
        assert not launch.called
        plugin.start_plugin(apply_update=False)
        assert plugin._toolbar_button is launcher and len(toolbar_launchers) == 1
        launcher.click()
        assert launch.call_count == 1
        plugin.close_plugin()
        assert plugin._toolbar_button is None and plugin._action is None
print('Passed:',version,'template discovery, project sets, guarded overrides/reset/persistence, DDS/ZIP, batch, collisions, missing-template alerts and legacy/native channels.')
