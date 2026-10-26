# Run PyInstaller on Windows to produce a Windows application.
from importlib.util import find_spec
from PyInstaller.utils.hooks import collect_all

extra_data = [("START_HERE.html", "."), ("START_HERE.md", "."),
              ("THIRD_PARTY.md", "."), ("LICENSE", ".")]
extra_binaries, extra_imports = [], []
if find_spec("sherpa_onnx") is not None:
    data, binaries, imports = collect_all("sherpa_onnx")
    extra_data += data
    extra_binaries += binaries
    extra_imports += imports

a = Analysis(
    ["launch.py"], pathex=[], binaries=extra_binaries, datas=extra_data,
    hiddenimports=extra_imports,
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.QtWebEngineQuick", "PySide6.QtQuick", "PySide6.QtQml"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Anato12Studio",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Anato12Studio")
