#! /usr/bin/env python3

import os, shutil, sys
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen


ROOT_PATH = Path(__file__).resolve().parent
DOWNLOAD_PATH = ROOT_PATH / 'downloads'
EXT_PATH = ROOT_PATH / 'ext'

if sys.platform == 'darwin':
    ZIP_URLS = ('https://www.a-quest.com/archive/package/aqtk10_mac_110.zip',
                'https://www.a-quest.com/archive/package/aqk2k_mac_300.zip')
else:
    ZIP_URLS = ('https://www.a-quest.com/archive/package/aqtk10_lnx_110.zip',
                'https://www.a-quest.com/archive/package/aqk2k_lnx_411.zip')
    INC_PATH = DOWNLOAD_PATH / 'include'
    LIB_PATH = DOWNLOAD_PATH / 'lib'


@contextmanager
def chdir(path):
    oldwd = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(oldwd)


def cmd(s):
    code = os.system(s)
    if code != 0:
        sys.exit(1)


def download_zip(url):
    with chdir(DOWNLOAD_PATH):
        fname = url.rpartition('/')[2]
        with urlopen(url) as rsp:
            if rsp.status != 200:
                raise RuntimeError('Failed to request %s' % url)
            (DOWNLOAD_PATH / fname).write_bytes(rsp.read())
        cmd("unzip '%s'" % fname)


def make_links():
    INC_PATH.mkdir(exist_ok=True)
    LIB_PATH.mkdir(exist_ok=True)
    for hpath in DOWNLOAD_PATH.glob('**/lib64/*.h'):
        lnkpath = INC_PATH / hpath.name
        lnkpath.unlink(missing_ok=True)
        lnkpath.symlink_to(Path('..') / hpath.relative_to(DOWNLOAD_PATH))
    for sopath in DOWNLOAD_PATH.glob('**/lib64/*.so.*'):
        lnkpath = LIB_PATH / sopath.name
        while lnkpath.suffix:
            lnkpath.unlink(missing_ok=True)
            lnkpath.symlink_to(Path('..') / sopath.relative_to(DOWNLOAD_PATH))
            lnkpath = LIB_PATH / lnkpath.stem


def build_aqtk_module():
    with chdir(EXT_PATH):
        cmd("'%s' setup.py build" % sys.executable)


def main():
    shutil.rmtree(str(DOWNLOAD_PATH), ignore_errors=True)
    shutil.rmtree(str(EXT_PATH / 'build'), ignore_errors=True)
    DOWNLOAD_PATH.mkdir()
    for url in ZIP_URLS:
        download_zip(url)
    if sys.platform != 'darwin':
        make_links()
    build_aqtk_module()


if __name__ == '__main__':
  main()
