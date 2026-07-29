# @Author: JogFeelingVi
# @Date: 2021-08-18 14:22:38
# @Last Modified by:   By JogFeelingVi
# @Last Modified time: 2021-08-18 14:22:38
import enum, re
from pathlib import PosixPath
from typing import List, Union
from . import osp


def style(msg: str = '', mt: int = 0, fc: int = 0, bg: int = 0) -> str:
    fmat = '\033[{code}{msg}\033[0m'
    switch = {0: '', 1: '{}m', 2: '{};{}m', 3: '{};{};{}m'}
    msg = f'{msg}'
    code = [x for x in [mt, fc, bg] if x != 0]
    code_f = str(switch.get(len(code))).format(*code)
    return fmat.format(code=code_f, msg=msg)


green = lambda m: style(m, fc=32)
pink = lambda m: style(m, fc=35)
blue = lambda m: style(m, fc=34)
red = lambda m: style(m, fc=31)
yello = lambda m: style(m, fc=33)


class call:
    __Fix_args = {'var': '1.02'}
    __files = None
    __fix = {
        'path': lambda k, v: call.__fix_path(k, v),
        'type': lambda k, v: call.__fix_type(k, v),
        'OxOO': lambda k, v: call.__fix_ohes(k, v),
    }
    __act = {
        'addx': lambda f: call.__act_addx(f),
        'rep': lambda f: call.__act_rep(f),
        'del': lambda f: call.__act_del(f),
        'dfx': lambda f: call.__act_delete(f),
        'sn': lambda i, f: call.__act_sn(i, f)
    }

    @staticmethod
    def pinfo(title: str, info: str):
        T = yello(title)
        I = blue(info)
        print(f'{T}: {I}')

    @staticmethod
    def pfile_L(id, n1, n2=None):
        '''
        The -type parameter is not used
        '''
        I = f'{yello(id)}'
        N1 = f'{pink(n1)}'
        N2 = f'{blue(n2)}' if n2 != None else ''
        if n2 is None:
            print(f'  {I}: {N1}')
        else:
            print(f'  {I}: {N1} > {N2}')

    @classmethod
    def __fix_path(cls, key, VALE):
        if (fix_item := osp.pathx(VALE)) is not None:
            cls.__Fix_args.update({key: fix_item})
        else:
            cls.__Fix_args.update({key: None})
            cls.pinfo('Error', 'Path Directory does not exist')

    @classmethod
    def __fix_type(cls, key, VALE):
        '''
            'type': ['mp3', 'avi'],
        '''
        if VALE is None:
            cls.__Fix_args.update({key: ['0xF']})
        elif isinstance(VALE, list):
            tmp = []
            for vx in VALE:
                if vx == 'f' or vx == 'd':
                    tmp.append(f'0x{str(vx).upper()}')
                else:
                    tmp.append(f'.{vx}')
            cls.__Fix_args.update({key: tmp})

    @classmethod
    def __fix_ohes(cls, key, VALE):
        cls.__Fix_args.update({key: VALE})

    def __init__(self, args: dict):
        #self.pinfo('Debug', f'Arges {args}')
        if (AT := type(args)) != dict:
            self.pinfo('Error',
                       f'Parameters must be of type dict, args-T is {AT}')
            return
        for k, v in args.items():
            if v is not None:
                if k in self.__fix.keys():
                    self.__fix[k](k, v)
                else:
                    self.__fix['OxOO'](k, v)
        self.pinfo('Debug', f'Arges {self.__Fix_args}')
        self.__files = self.__find()

    @classmethod
    def __find(cls):
        ospif = osp.ifile
        _p = cls.__Fix_args.get('path')
        if _p is None:
            return
        if (tmp := osp.find(_p)) is None:
            cls.pinfo('Error', f'{_p} There is no documentation')
            return
        elif type(tmp) == list:
            if 'type' not in cls.__Fix_args.keys():
                cls.pinfo('Warning', 'The -type parameter is not used')
                tmp = [ospif(x) for x in tmp]
            else:
                sufx = cls.__Fix_args['type']
                typed = {
                    '0xF':
                    lambda t: [ospif(x) for x in t if ospif(x).file.is_file()],
                    '0xD':
                    lambda t: [ospif(x) for x in t if ospif(x).file.is_dir()],
                    '0xC':
                    lambda t: [ospif(x) for x in t if ospif(x).sufx in sufx]
                }
                if sufx & typed.keys():
                    tmp = typed[sufx[0]](tmp)
                else:
                    tmp = typed['0xC'](tmp)

            if 'filter' in cls.__Fix_args.keys():
                regx = cls.__Fix_args['filter']
                regxs = lambda Sx: re.search(regx, Sx)
                tmp = [x for x in tmp if regxs(x.file.name) != None]
            flen = tmp.__len__()
            cls.pinfo('Find', f'{flen} files found')
            return tmp

    @staticmethod
    def __r4(bit: int = 4):
        bit = [4, bit][7 >= bit >= 3]
        from random import randint as rint
        bits = '{}' * bit
        fxst = f'-{bits}'
        spflag = 26 / bit
        Lc = list('aBc0efg2ijk3mNo7Qrs9uvWyz1')
        groud = [(int(x * spflag), int(x * spflag + spflag))
                 for x in range(bit)]
        str4 = [Lc[rint(x[0], x[1] - 1)] for x in groud]
        return fxst.format(*str4)

    @classmethod
    def __act_save(cls):
        return cls.__Fix_args['save']

    @classmethod
    def __act_show(cls, files: List[osp.ifile]):
        if files is None:
            cls.pinfo('Warning', 'File list is empty')
            return
        elif type(files) is list:
            for key in cls.__act.keys():
                if key in cls.__Fix_args.keys():
                    return
            for i, ifs in enumerate(files):
                cls.pfile_L(i, ifs.file.name)

    @classmethod
    def __act_add(cls, file: osp.ifile):
        comar = cls.__Fix_args['add'].split('@')
        sx, ix = [[comar[-1], 0], comar][len(comar) == 2]
        ix = [ix, int(ix)][type(ix) is str]
        tmp = list(file.name)
        tmp.insert(ix, sx)
        tmp = ''.join(tmp)
        print(f'debug {sx} {ix}')
        return tmp

    @classmethod
    def __act_addx(cls, file: osp.ifile):
        sx, ix = cls.__Fix_args['addx']
        ix = [ix, int(ix)][type(ix) is str]
        tmp = list(file.name)
        tmp.insert(ix, sx)
        tmp = ''.join(tmp)
        return tmp

    @classmethod
    def __act_del(cls, file: osp.ifile):
        comar = cls.__Fix_args['del']
        tmp = file.name
        for D in comar:
            #tmp = tmp.replace(D, '')
            tmp = re.sub(D, '', tmp, 0)
        return tmp

    @classmethod
    def __act_rep(cls, file: osp.ifile):
        comar = cls.__Fix_args['rep']
        if len(comar) > 2:
            cls.pinfo('Error', '-r xxx:yyy Parameter error')
            return
        else:
            o, n = comar
            tmp = file.name
            tmp = re.sub(o, n, tmp, 0)
            return tmp

    @classmethod
    def __act_delete(cls, file: osp.ifile):
        dxpath = osp.plib.PosixPath(cls.__Fix_args['dfx'])
        if dxpath.exists() == False:
            cls.pinfo('Error', '{dxpath} Path does not exist')
        else:
            with open(dxpath, 'r') as reads:
                lines = reads.read().split('\n')
                tmp = file.name
                for L in lines:
                    tmp = tmp.replace(L, '')
                return tmp

    @classmethod
    def __act_sn(cls, index: int, file: osp.ifile):
        ix = index + 1
        fls = int(cls.__Fix_args['sn'])
        fls = fls if fls >= 2 else 2
        fmz = f'{{s:0{fls}}}'
        tmp = file.name
        match = re.match(r'[\d]{2,}[-]', tmp)
        if match is not None:
            return tmp
        else:
            tmp = f'{fmz.format(s=ix)}-{tmp}'
            return tmp

    @classmethod
    def __act_r4(cls, oName: str):
        if 'ucode' in cls.__Fix_args.keys():
            r4 = cls.__Fix_args['ucode']
            tmp = f'{oName}{cls.__r4(int(r4))}'
            return tmp
        else:
            return oName

    def action(self):
        if self.__files is None:
            return
        actkeys = 'addx,del,rep,dfx,sn'.split(',')
        for key in actkeys:
            if key in self.__Fix_args.keys():
                for i, ifs in enumerate(self.__files):
                    o_Name = ifs.name
                    if key != 'sn':
                        n_Name = self.__act[key](ifs)
                    else:
                        n_Name = self.__act[key](i, ifs)
                    # del fast string .
                    if n_Name[0] in list(' .,') and len(n_Name) >= 2:
                        n_Name = n_Name[1:]
                    # add r4 shibiema
                    n_Name = self.__act_r4(n_Name)
                    if o_Name != n_Name:
                        nPath = ifs.nPath(n_Name)
                        # show diff file name
                        self.pfile_L(i, o_Name, n_Name)
                        if self.__act_save() and nPath != None:
                            ifs.file.rename(nPath)
                    else:
                        self.pfile_L(i, o_Name)
                #self.__act[key](self.__files)
        if self.__Fix_args['show'] == True:
            self.__act_show(self.__files)
