import os, sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent.resolve()

if sys.platform == 'darwin':
    FRAMEWORKS = (ROOT_PATH / 'downloads/aqtk10_mac/AquesTalk.framework',
                  ROOT_PATH / 'downloads/aqk2k_mac/AqKanji2Koe.framework')
    RPATH = ':'.join({ str(x.parent) for x in FRAMEWORKS })

    os.environ['CFLAGS'] = ' '.join(['-I%s' % (x / 'Headers') for x in FRAMEWORKS])
    os.environ['LDFLAGS'] = ' '.join(['-rpath %s -F%s -framework %s' % (x.parent, x.parent, x.stem)
                                      for x in FRAMEWORKS])
    os.environ['ARCHFLAGS'] = '-arch x86_64'

from distutils.core import setup, Extension

if sys.platform == 'darwin':
    module1 = Extension('aqtk', sources = ['aqtk.c'])
else:
    module1 = Extension('aqtk',
                        sources = ['aqtk.c'],
                        include_dirs = [str(ROOT_PATH / 'downloads/include')],
                        library_dirs = [str(ROOT_PATH / 'downloads/lib')],
                        runtime_library_dirs = [str(ROOT_PATH / 'downloads/lib')],
                        libraries = ['AquesTalk10', 'AqKanji2Koe', 'stdc++'])

setup (name = 'aqtk',
       version = '1.0',
       description = 'Python binding of AquesTalk',
       ext_modules = [module1])
