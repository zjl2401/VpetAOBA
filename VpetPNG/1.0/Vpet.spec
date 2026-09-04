# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_root = Path(SPECPATH)


def _data_pair(src: Path, dest: str):
    return (str(src), dest)


datas = [
    _data_pair(spec_root / "assets", "assets"),
    _data_pair(spec_root / "gallery", "gallery"),
    _data_pair(spec_root / "word_banks", "word_banks"),
]
for name in ("app_icon.png", "app_icon1.jpg", "border1.jpg", "border5.jpg"):
    p = spec_root / name
    if p.is_file():
        datas.append(_data_pair(p, "."))
type_cache = spec_root / "data" / "audio" / "type_cache.wav"
if type_cache.is_file():
    datas.append(_data_pair(type_cache, "data/audio"))

a = Analysis(
    [str(spec_root / "vpet_app.py")],
    pathex=[str(spec_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "pystray",
        "PIL.ImageTk",
        "pygame",
        "imageio_ffmpeg",
        "pet",
        "vpet_launcher",
        "panel_decor",
        "home_cottage",
        "voice_audio",
        "voice_system",
        "bundled_paths",
        "media_bundled",
        "pet_id_cloud",
        "app_scene_desktop",
        "rhythm_chart_editor",
        "pet_outfit",
        "peer_friendship",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Vpet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(spec_root / "app_icon.ico")],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Vpet",
)
