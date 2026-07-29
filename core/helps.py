# @Author: JogFeelingVi
# @Date: 2021-08-18 11:47:30
# @Last Modified by:   By JogFeelingVi
# @Last Modified time: 2021-08-18 11:47:30
from enum import Enum as __EN


class strings(__EN):
    dels = 'Delete specified characters，Ex -d xxx or -d xxx yyy zzz'
    paths = 'Specify the file path, which can be a folder or file name'
    test = 'NULL'
    addto = 'Add string to file name -a ddd or -a ddd -5'
    reps = 'Replace the string specified in the file name -r xxx yyyy'
    types = 'Specify file type -t mp4 or -t "mp4,jpg"'
    delxs = 'Read the file to delete the list, then modify the file -dx ~/deldict[file]'
    shows = 'show file list exp -s'
    desct = 'Multi-file renaming by jogfeelingvi'
    filter = 'Regular expression filtering file list'
