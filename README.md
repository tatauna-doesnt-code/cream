<p align="center">
  <img src="docs/assets/cream-logo.png" width="240" alt="CREAM">
</p>

**Color Replacement & Export Automation Manager**

CREAM turns your Substance 3D Painter textures into a **Trackmania 2020 skin ZIP** on Windows.

| Workflow | Painter version |
| --- | --- |
| Style the in-game skin name and export a ZIP with DDS textures in one click | **8.1.2+** |
| Batch-export versions of a skin with custom text and colors | **10.0+** · **10.1.2+ recommended** for more stable layer editing |

## Quick start

1. **Install.** Download **CREAM-plugin.zip** from [Releases](https://github.com/tatauna-doesnt-code/cream/releases) and extract it. Save your work, close Painter and run **Install.cmd**.
2. **Open.** Reopen Painter, enable **Python → cream** and open your saved project. Click the **c** in Painter’s Plugins toolbar or choose **Window → CREAM**.
3. **Choose a folder.** In **CREAM → Settings → Save ZIPs to**, choose where to save your skin. For game uploads, use `Trackmania/Skins/Models/CarSport` directly.
4. **Export.** In **Textures**, choose an export template and check the images you want. In **Skin ZIPfile name**, enter a name and click **Export current skin**.

Leave **Batch** empty to export the car as it looks in Painter. A single export needs no special layers.

<details>
<summary>Updates and manual installation</summary>

Choose **CREAM → Settings → Check for updates** and follow the restart prompt if one appears. To upgrade from an older package name, close Painter and run the new **Install.cmd** once. It backs up the old installation.

To install manually, copy the entire `cream` folder, including its fonts and DDS converter, to `Documents/Adobe/Adobe Substance 3D Painter/python/plugins`.

</details>

## Export settings

### Textures and resolution

An **export template** defines the images Painter produces. CREAM selects **TM2020** when it finds one match. Check a texture set to export all its images, or expand it to pick individual maps.

Choose a resolution for the whole set or for any map inside it. **Source / template** uses Painter’s dimensions. **Wheels** defaults to **512 × 2048** because its 1:4 proportions keep shadows and bevels from stretching.

To reuse an existing skin, choose **Batch → Base skin ZIP (optional)**. Its textures must sit at the top level of the ZIP. CREAM replaces the selected textures and keeps the other files. This also works for a single export.

<details>
<summary>Texture suffixes and DDS compression</summary>

The template controls channel packing and normal direction. CREAM writes DDS textures without mipmaps.

| Filename suffix | Texture contents | DDS |
| --- | --- | --- |
| `_B` | Base color | BC1 |
| `_R` | Roughness in red, metallic in green | BC5 |
| `_I` | Emissive color and alpha | BC3 |
| `_N` | Normals | BC5 |
| `_CoatR` | Coat roughness | BC4 |
| `_DirtMask` | Dirt mask | BC4 |
| `_AO` | Ambient occlusion | BC1 |

Unknown suffixes default to BC3. Hover over a warning to see how an output differs from the table. Use the restore icon to undo a suffix or compression edit.

</details>

### In-game skin name

In **Skin ZIPfile name**, replace `skin` with your filename. Select text to style it and check the in-game preview below. Text colors use three hex digits, such as `$F80`. CREAM numbers duplicate filenames automatically.

## Batch export

### Prepare the Painter project

Set up only the parts of the car you want to change. CREAM uses the same texture selection for every entry.

| To customize | Set this up in Painter |
| --- | --- |
| Text on the car | Add a **Fill effect** to a layer mask. Choose a **Font** as its grayscale input and name the effect `PLAYER_NAME`. Set the size and placement in Painter. CREAM updates every matching effect. |
| Theme colors | Create a **Fill layer** with a solid **Base Color** and name it `PLAYER_COLOR1`. For additional colors, use `PLAYER_COLOR2` and `PLAYER_COLOR3`. |

CREAM skips **Glass** when applying text or colors. A warning beside a Batch column identifies a missing layer or effect.

### Add entries and export

1. In **Batch**, click **Add a batch entry**. Enter custom text (up to 20 characters), a color such as `#FF8030`, or both. Blank fields keep the project’s original values.
2. In the filename editor, insert **ZIP name** to use each entry’s name. For example, `Team - {name}` produces `Team - Joseph.zip`. The text color picker can use each entry’s first or second color.
3. To check a variation in Painter, highlight its row and click **Preview highlighted skin**. Click **Restore original** to finish previewing.
4. Check the rows you want and export. Each checked row produces one ZIP. **Clear batch** returns to single-skin export.

<details>
<summary>Import entries from CSV or XLSX</summary>

Choose **Import CSV / XLSX…**. Use column headers and one row per skin. Match a text column, a color column, or both. For color palettes, leave **Player name** blank. You can also map a ZIP name, row ID and export selection.

For XLSX, use the first worksheet and enter values instead of formulas. Reimport spreadsheet-only lists after restarting Painter.

</details>

<details>
<summary>Cancel or resume a batch</summary>

**Cancel safely** finishes the current operation and keeps completed ZIPs. To continue, reopen the same project with the same batch and settings. Choose **Resume a previous batch…** and select its report from `_CREAM_reports` in your output folder. CREAM unchecks completed entries whose ZIPs still exist. Review the remaining rows and export.

</details>

## Painter compatibility

The minimum versions above apply to Adobe and Steam editions. On Painter 8–9, use a template saved in a library. These versions may render the whole template for each selected map, which takes longer. CREAM supports single-tile projects and templates that export directly to one folder. UDIMs and material layering are unsupported.

### Tested in Painter

Results cover tests inside Painter across CREAM releases.

**✓** confirmed · **✓\*** expected to work, awaiting confirmation · **–** untested · **✗** unsupported or confirmed failure

| Major feature | 9.1.2 | 10.0.0 | 10.1.2 | 11.1.3 | 12.1.3 |
| --- | :---: | :---: | :---: | :---: | :---: |
| Export a finished Trackmania skin ZIP | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Export+a+finished+Trackmania+skin+ZIP+%E2%80%94+Painter+9.1.2&feature=Export+a+finished+Trackmania+skin+ZIP&painter=9.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Export+a+finished+Trackmania+skin+ZIP+%E2%80%94+Painter+10.0.0&feature=Export+a+finished+Trackmania+skin+ZIP&painter=10.0.0) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Export+a+finished+Trackmania+skin+ZIP+%E2%80%94+Painter+10.1.2&feature=Export+a+finished+Trackmania+skin+ZIP&painter=10.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Export+a+finished+Trackmania+skin+ZIP+%E2%80%94+Painter+11.1.3&feature=Export+a+finished+Trackmania+skin+ZIP&painter=11.1.3) | [✓](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Export+a+finished+Trackmania+skin+ZIP+%E2%80%94+Painter+12.1.3&feature=Export+a+finished+Trackmania+skin+ZIP&painter=12.1.3) |
| Style and preview the in-game skin name | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Style+and+preview+the+in-game+skin+name+%E2%80%94+Painter+9.1.2&feature=Style+and+preview+the+in-game+skin+name&painter=9.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Style+and+preview+the+in-game+skin+name+%E2%80%94+Painter+10.0.0&feature=Style+and+preview+the+in-game+skin+name&painter=10.0.0) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Style+and+preview+the+in-game+skin+name+%E2%80%94+Painter+10.1.2&feature=Style+and+preview+the+in-game+skin+name&painter=10.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Style+and+preview+the+in-game+skin+name+%E2%80%94+Painter+11.1.3&feature=Style+and+preview+the+in-game+skin+name&painter=11.1.3) | [✓](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Style+and+preview+the+in-game+skin+name+%E2%80%94+Painter+12.1.3&feature=Style+and+preview+the+in-game+skin+name&painter=12.1.3) |
| Reuse a base skin ZIP and replace selected textures | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Reuse+a+base+skin+ZIP+and+replace+selected+textures+%E2%80%94+Painter+9.1.2&feature=Reuse+a+base+skin+ZIP+and+replace+selected+textures&painter=9.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Reuse+a+base+skin+ZIP+and+replace+selected+textures+%E2%80%94+Painter+10.0.0&feature=Reuse+a+base+skin+ZIP+and+replace+selected+textures&painter=10.0.0) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Reuse+a+base+skin+ZIP+and+replace+selected+textures+%E2%80%94+Painter+10.1.2&feature=Reuse+a+base+skin+ZIP+and+replace+selected+textures&painter=10.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Reuse+a+base+skin+ZIP+and+replace+selected+textures+%E2%80%94+Painter+11.1.3&feature=Reuse+a+base+skin+ZIP+and+replace+selected+textures&painter=11.1.3) | [✓](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Reuse+a+base+skin+ZIP+and+replace+selected+textures+%E2%80%94+Painter+12.1.3&feature=Reuse+a+base+skin+ZIP+and+replace+selected+textures&painter=12.1.3) |
| Batch-export skins with custom text and colors | [✗](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Batch-export+skins+with+custom+text+and+colors+%E2%80%94+Painter+9.1.2&feature=Batch-export+skins+with+custom+text+and+colors&painter=9.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Batch-export+skins+with+custom+text+and+colors+%E2%80%94+Painter+10.0.0&feature=Batch-export+skins+with+custom+text+and+colors&painter=10.0.0) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Batch-export+skins+with+custom+text+and+colors+%E2%80%94+Painter+10.1.2&feature=Batch-export+skins+with+custom+text+and+colors&painter=10.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Batch-export+skins+with+custom+text+and+colors+%E2%80%94+Painter+11.1.3&feature=Batch-export+skins+with+custom+text+and+colors&painter=11.1.3) | [✓](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Batch-export+skins+with+custom+text+and+colors+%E2%80%94+Painter+12.1.3&feature=Batch-export+skins+with+custom+text+and+colors&painter=12.1.3) |
| Import batch entries from CSV or XLSX | [–](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Import+batch+entries+from+CSV+or+XLSX+%E2%80%94+Painter+9.1.2&feature=Import+batch+entries+from+CSV+or+XLSX&painter=9.1.2) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Import+batch+entries+from+CSV+or+XLSX+%E2%80%94+Painter+10.0.0&feature=Import+batch+entries+from+CSV+or+XLSX&painter=10.0.0) | [✓\*](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Import+batch+entries+from+CSV+or+XLSX+%E2%80%94+Painter+10.1.2&feature=Import+batch+entries+from+CSV+or+XLSX&painter=10.1.2) | [–](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Import+batch+entries+from+CSV+or+XLSX+%E2%80%94+Painter+11.1.3&feature=Import+batch+entries+from+CSV+or+XLSX&painter=11.1.3) | [✓](https://github.com/tatauna-doesnt-code/cream/issues/new?template=compatibility_test.yml&title=%5BCompatibility%5D+Import+batch+entries+from+CSV+or+XLSX+%E2%80%94+Painter+12.1.3&feature=Import+batch+entries+from+CSV+or+XLSX&painter=12.1.3) |

Click a symbol to report your result on GitHub. Written evidence is required. Attachments are optional.

On **11.1.3**, testing confirmed DDS conversion before a missing channel interrupted export. CREAM now checks for known missing channels. A completed ZIP still awaits confirmation on this version.

## Troubleshooting

- **Missing template?** Check its name in Painter’s **Export Textures** window, then click **Refresh** in **CREAM → Textures**. On Painter 8–9, save the template to a library first.
- **Missing channel?** Check the map named in the error. If your skin has no glowing parts, you can uncheck the emissive map (`_I`). If you need it, check the template mapping and add its required channel to the texture set. Painter’s **Log** panel shows the **MapExporter** error.
- **Stuck in a preview?** Open the original project and choose **CREAM → Logs → Restore original / recover project**. To keep the current values, use **Batch → Detach from project**. Detaching ends recovery for that preview. Saving afterward keeps the changes on the car.
- **Skin previews but won’t upload?** Move the ZIP directly into `Trackmania/Skins/Models/CarSport` and try again. Uploads from subfolders can fail.

## Project information

### Development and support

Use **Dev.cmd** to test changes locally. [Development guide](docs/development.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

For bugs, include your CREAM and Painter versions, the steps you took and the relevant log message. Remove personal paths and private data. [Report a bug](https://github.com/tatauna-doesnt-code/cream/issues) · [Report a security issue privately](SECURITY.md)

### Special thanks

Thanks to our beta testers **LTW**, **devdabomber**, **Lvyathan**, **notavailablenam**, **Mordecai**, and **panth**.

### License

CREAM is licensed under [GPL-3.0-only](LICENSE). Bundled fonts and Microsoft texconv have their own [third-party notices](THIRD_PARTY_NOTICES.md).
