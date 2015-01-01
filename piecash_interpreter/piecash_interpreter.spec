# -*- mode: python -*-
a = Analysis(['piecash_interpreter.py'],
             pathex=['C:\\Users\\sdementen\\Projects\\piecash-dev'],
             hiddenimports=['piecash'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='piecash_interpreter.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
