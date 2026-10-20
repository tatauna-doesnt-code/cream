# Changes

## 1.1.2

- Request Normal OpenGL from Painter at export time, including with the original
  TM2020 DirectX template. Already-correct OpenGL templates remain unchanged.
- Remove post-export green inversion. DDS conversion preserves the exported green
  channel. Old batch reports cannot be resumed across this pipeline change.
- Document how to configure the saved TM2020 template for manual exports.

## 1.1.1

- Define explicit infinite padding for the inline export preset. Fixes
  “padding algorithm could not be resolved” when validating or exporting maps
  whose resource preset does not provide a padding algorithm.

## 1.1.0

- Invert normal-map green after DDS BC5 conversion.
- Add private GitHub update checks and staged installation with backup.
