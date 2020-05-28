# -*- mode: python -*-

block_cipher = None


a = Analysis(['labelImg.py'],
             pathex=['C:/Program Files/Python35/Lib/site-packages/PyQt5/Qt/bin', 'C:/Program Files/Python35/Lib/site-packages', 'D:\projects\labelImg'],
             binaries=[],
             datas=[],
             hiddenimports=["cv2"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
		  
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='labelImg',
          debug=True,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='labelImg')
