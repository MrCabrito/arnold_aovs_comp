# Arnold AOV Tool

The tool will separate all the arnold AOV's found in the render for a better comp or check the passes are correct.

## Installation

Install Arnold AOV Tool in nuke.

1. Close Nuke

2. Download the Win RAR file.

3. Uncompress the Win RAR file.

4. Copy the uncompressed folder into the .nuke folder, that is found inside the user folder.

5. Open or create a file called menu.py inside the .nuke folder.

6. Inside the file add the next lines:

```python
  import arnold_aovs_comp.aovs_UI
  toolbar = nuke.toolbar('Nodes')
  toolbar.addCommand('AOVs', 'arnold_aovs_comp.aovs_UI.main()')
```

7. Open Nuke, you will get a button in the side menu or in the tab menu you can find it with the name AOVs

## Authors

- Abraham González [@Abraham](https://www.github.com/MrCabrito)

## Appendix

It works for Nuke 13 or higher.

Only works with Arnold Renders.

## Documentation

[Documentation](https://1drv.ms/w/s!AuKLApdKflwPwikR-5Uh21RSufvR?e=cK2xSy)
