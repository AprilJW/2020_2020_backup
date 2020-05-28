# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\main.py'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
		  Tree('src', prefix=''),
          name='labelImg',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
