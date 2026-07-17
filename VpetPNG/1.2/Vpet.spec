# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\vpet_app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\assets', 'assets'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\gallery', 'gallery'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\word_banks', 'word_banks'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\app_icon.png', '.'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\app_icon1.jpg', '.'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\border1.jpg', '.'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\border5.jpg', '.'), ('C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\data\\audio\\type_cache.wav', 'data/audio')],
    hiddenimports=['pystray', 'PIL.ImageTk', 'pygame', 'imageio_ffmpeg', 'pet', 'vpet_launcher', 'panel_decor', 'voice_audio', 'voice_system', 'bundled_paths', 'media_bundled', 'pet_id_cloud'],
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
    name='Vpet',
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
    icon=['C:\\Users\\36255\\Desktop\\VpetAOBA\\VpetPNG\\1.2\\app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Vpet',
)
