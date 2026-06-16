Place your Windows icon file here as:

  icon.ico

Then build the EXE with:

  py -m pip install pyinstaller
  pyinstaller FlashDrumDesigner.spec

The icon is used for:
- The .exe file icon in Windows Explorer
- The application window/taskbar icon at runtime