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
sp.ui.delete_ui_element = lambda obj: obj.deleteLater()
sp.project.is_open = lambda: True
sp.project.is_busy = lambda: False
sp.project.is_in_edition_state = lambda: True
sets = ['Body','Tyres']
stack = types.SimpleNamespace(name=lambda: '')
sp.textureset.all_texture_sets = lambda: [types.SimpleNamespace(name=name if version >= (11,0,0) else lambda n=name:n,
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
sp.resource.search = lambda q: [types.SimpleNamespace(identifier=lambda p=p:types.SimpleNamespace(name=p['name'],url=lambda:p['url']), type=lambda:1) for p in catalog]
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
from cream import ui, bootstrap, template_export, compatibility, core

with tempfile.TemporaryDirectory() as folder, patch.object(ui,'DATA',Path(folder)), patch.object(bootstrap,'DATA',Path(folder)):
    sp.project.file_path=lambda:str(Path(folder)/'skin.spp')
    window=ui.Window(auto_update=False)
    window.show()
    app.processEvents()
    texture=window.texture_sets
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
    assert '*' in texture.tab_label.text() and texture.tab_label.font().italic()
    assert not compression.alert.toolTip()
    compression.input.setCurrentText('BC1');compression.edited()
    assert compression.alert.toolTip() and not texture.tab_warning.isHidden()
    point = QtCore.QPointF(1, 1)
    texture.tab_warning.enterEvent(QtGui.QEnterEvent(point, point, point))
    assert W.QToolTip.text() == texture.tab_warning.toolTip()
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
    assert '*' not in texture.tab_label.text()
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
    window.restore_reload_state({'rows':[{'id':'1','line':1,'name':'Player','stem':'Player','colors':[None,None,None]}],
                                 'loaded_sheet':None,'checked':[True],'selected':0,'log':''})
    window.start();finish()
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
    window.grab().save(str(ROOT/'dist'/('template-overrides-'+'.'.join(map(str,version))+'.png')))
    # Missing default is a visible, recoverable state; any installed template can be selected.
    catalog[:]=[catalog[1]]
    texture.template.setCurrentIndex(0)
    texture.pending=None
    texture.loaded_url=None
    texture.reload(force=True)
    assert texture.problem and not texture.tab_warning.isHidden()
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
    window.stop_background_tasks()
    window.hide()
print('Passed:',version,'template discovery, project sets, guarded overrides/reset/persistence, DDS/ZIP, batch, collisions, missing-template alerts and legacy/native channels.')
