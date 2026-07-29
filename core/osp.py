# @Author: JogFeelingVi
# @Date: 2021-08-18 15:12:58
# @Last Modified by:   By JogFeelingVi
# @Last Modified time: 2021-08-18 15:12:58
import pathlib as plib
from pickle import FALSE
from typing import Union


def pathx(p: str = '~/Downloads'):
    flg = p[0]
    fixs = {
        '~': lambda x: plib.Path(x).expanduser(),
        '.': lambda x: plib.Path(x).absolute(),
        '/': lambda x: plib.Path(x),
    }
    path = fixs[flg](p)
    return path if path.exists() else None


def find(p: str) -> list:
    files = []
    _p = plib.PosixPath(p)
    if p is not None:
        if _p.is_file() == True:
            files = [p]
        elif _p.is_dir():
            files = [x for x in _p.glob('*')]  # and x.name[0] not in ['.']
            #if x.is_file() and x.name[0] not in ['.']
    return files


class ifile:

    def __init__(self, path: str) -> None:
        self.file = plib.PosixPath(path)
        self.sufx = self.file.suffix
        self.name = self.file.name.replace(self.sufx, '')

    def nPath(self, nName: str):
        '''
        file new name 
            n2p = osp.plib.Path(ifs.file.parent, n2)
        '''
        nPx = plib.Path(self.file.parent, f'{nName}{self.sufx}')
        exfile = self.file.parent.glob('*.*')
        nPx_exists = []
        for exf in exfile:
            nPx_exists.append(1 if exf == nPx else 0)
        if sum(nPx_exists) == 0:
            return nPx
        else:
            return None
