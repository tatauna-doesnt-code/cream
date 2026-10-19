import copy
from enum import Enum
from pathlib import Path
import sys
import types
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sp = types.ModuleType('substance_painter')
sp.__path__ = []
sys.modules['substance_painter'] = sp
for name in ['project', 'layerstack', 'textureset', 'colormanagement', 'source', 'export']:
    module = types.ModuleType('substance_painter.' + name)
    setattr(sp, name, module)
    sys.modules[module.__name__] = module

class Space(Enum):
    sRGB = 1
    Raw = 2

class Color:
    def __init__(self, *rgb, color_space=None):
        self.value_raw = rgb
        self.color_space = color_space

class Font:
    def __init__(self):
        self.resource_id = types.SimpleNamespace(url=lambda: 'resource://font')
        self.params = types.SimpleNamespace(text='Original', size=0.25, color='black', offset=(0.1, 0.2))
    def get_parameters(self): return copy.copy(self.params)
    def set_parameters(self, params): self.params = params

class Uniform:
    def __init__(self): self.color = Color(0.25, 0.5, 0.75, color_space=Space.sRGB)
    def get_color(self): return self.color
    def set_color(self, color): self.color = color

class Node:
    def __init__(self, name, source=None, children=None, masks=None):
        self.name = name
        self.source = source
        self.children = children or []
        self.masks = masks or []
    def get_name(self): return self.name
    def uid(self): return id(self)
    def get_source(self, channel=None): return self.source

class Layer(Node):
    def content_effects(self): return []
    def mask_effects(self): return self.masks
    def has_mask(self): return bool(self.masks)

class Group(Layer):
    def sub_layers(self): return self.children

class Fill(Layer): pass
class Effect(Node):
    def is_in_mask_stack(self): return True

class Scope:
    def __init__(self, name): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

sp.source.SourceFont = Font
sp.source.SourceUniformColor = Uniform
sp.colormanagement.Color = Color
sp.colormanagement.GenericColorSpace = Space
sp.layerstack.GroupLayerNode = Group
sp.layerstack.LayerNode = Layer
sp.layerstack.FillLayerNode = Fill
sp.layerstack.FillEffectNode = Effect
sp.layerstack.ScopedModification = Scope
sp.textureset.ChannelType = types.SimpleNamespace(BaseColor='base')
sp.project.is_open = lambda: True
sp.project.file_path = lambda: 'example.spp'
from kr7_batch import painter

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.fonts = [Font() for _ in range(4)]
        self.color = Uniform()
        self.glass = Font()
        self.root = Group('Names', children=[Fill('PLAYER_COLOR1', self.color)],
                          masks=[Effect('PLAYER_NAME', source=f) for f in self.fonts])
        stack = types.SimpleNamespace(name=lambda: '', roots=[self.root])
        glass_stack = types.SimpleNamespace(name=lambda: '', roots=[Layer('Names', masks=[Effect('PLAYER_NAME', self.glass)])])
        sp.textureset.all_texture_sets = lambda: [types.SimpleNamespace(name='Skin', all_stacks=lambda: [stack]),
                                                  types.SimpleNamespace(name='Glass', all_stacks=lambda: [glass_stack])]
        sp.layerstack.get_root_layer_nodes = lambda s: s.roots

    def test_all_masks_and_colors_restore_exactly(self):
        saved = painter.snapshot()
        self.assertEqual(len(saved['targets']), 5)
        painter.apply(saved, {'name': 'Joseph', 'colors': ['#FF0000', None, None]})
        self.assertTrue(all(f.params.text == 'Joseph' for f in self.fonts))
        self.assertEqual(self.glass.params.text, 'Original')
        self.assertEqual(self.color.color.value_raw, (1.0, 0.0, 0.0))
        self.assertEqual(self.fonts[0].params.size, 0.25)
        self.assertEqual(self.fonts[0].params.color, 'black')
        painter.apply(saved, {'name': 'Next', 'colors': [None, None, None]})
        self.assertEqual(self.color.color.value_raw, (0.25, 0.5, 0.75))
        painter.apply(saved)
        self.assertTrue(all(f.params.text == 'Original' for f in self.fonts))

    def test_changed_structure_aborts_before_mutation(self):
        saved = painter.snapshot()
        self.root.children[0].name = 'Renamed'
        with self.assertRaises(ValueError):
            painter.apply(saved, {'name': 'Wrong', 'colors': ['#FF0000', None, None]})
        self.assertTrue(all(f.params.text == 'Original' for f in self.fonts))

    def test_anchor_named_like_color_layer_is_ignored(self):
        self.root.children[0].content_effects = lambda: [Node('PLAYER_COLOR1')]
        saved = painter.snapshot()
        self.assertEqual(len(saved['targets']), 5)
        painter.apply(saved, {'name': 'Joseph', 'colors': ['#FF0000', None, None]})
        self.assertEqual(self.color.color.value_raw, (1.0, 0.0, 0.0))

    def test_export_dimensions_and_preset_unchanged(self):
        maps = [{'fileName':'$textureSet_N', 'channels':[{'srcMapName':'Normal_DirectX'}], 'parameters':{'fileFormat':'tga'}}]
        config = painter.export_config(maps, 'Wheels', 'N', 2048, 'output')
        self.assertEqual(config['exportPresets'][0]['maps'][0]['parameters']['sizeLog2'], [9,11])
        self.assertEqual(maps[0]['parameters']['fileFormat'], 'tga')
        self.assertEqual(config['exportPresets'][0]['maps'][0]['channels'], maps[0]['channels'])

    def test_padding_is_explicit_without_mutating_resource_maps(self):
        # Resource map definitions can omit the export dialog's padding setting.
        maps = [{'fileName': '$textureSet_B', 'channels': [], 'parameters': {}}]
        config = painter.export_config(maps, 'Skin', 'B', 2048, 'output')
        self.assertEqual(config['exportParameters'][0]['parameters']['paddingAlgorithm'], 'infinite')
        self.assertEqual(config['exportPresets'][0]['maps'][0]['parameters']['paddingAlgorithm'], 'infinite')
        self.assertEqual(maps[0]['parameters'], {})

if __name__ == '__main__':
    unittest.main(verbosity=2)
