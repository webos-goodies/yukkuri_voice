import os
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parent.parent.resolve()
FRAMEWORKS = (ROOT_PATH / 'downloads/aqtk10_mac/AquesTalk.framework',
              ROOT_PATH / 'downloads/aqk2k_mac/AqKanji2Koe.framework')
RPATH = ':'.join({ str(x.parent) for x in FRAMEWORKS })

os.environ['CFLAGS'] = ' '.join(['-I%s' % (x / 'Headers') for x in FRAMEWORKS])
os.environ['LDFLAGS'] = ' '.join(['-rpath %s -F%s -framework %s' % (x.parent, x.parent, x.stem)
                                  for x in FRAMEWORKS])
os.environ['ARCHFLAGS'] = '-arch x86_64'

from distutils.core import setup, Extension

module1 = Extension('aqtk', sources = ['aqtk.c'])

setup (name = 'aqtk',
       version = '1.0',
       description = 'Python binding of AquesTalk',
       ext_modules = [module1])
