import os.path as opath
import platform
import os
from functools import reduce


if platform.system().startswith('Darwin'):
    DATA_HOME = reduce(opath.join, [opath.expanduser("~"), 'Dropbox', '_researchData', 'Mule_BLE'])
else:
    DATA_HOME = reduce(opath.join, [opath.expanduser("~"), 'research', '_data', 'Mule_BLE'])

ef_dpath = opath.join(DATA_HOME, 'z_ExternalFiles')
assert opath.exists(ef_dpath)


dp_dpath = opath.join(DATA_HOME, 'a_DataProcessing')
pf_dpath = opath.join(DATA_HOME, 'w_ProcessedFiles')

dir_paths = [DATA_HOME,
                dp_dpath,




                pf_dpath
             ]
for dpath in dir_paths:
    if not opath.exists(dpath):
        os.mkdir(dpath)


