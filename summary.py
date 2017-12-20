import os.path as opath
import os, fnmatch
import csv
import numpy as np


def run():
    prefix_dpaths = {}
    for dn in os.listdir('z_data'):
        if not dn.startswith('_'):
            continue
        prefix = dn[len('_MA-'):-len('-R0')]
        if prefix not in prefix_dpaths:
            prefix_dpaths[prefix] = []
        prefix_dpaths[prefix].append(opath.join('z_data', dn))
    for prefix in prefix_dpaths:
        numBK = None
        dateHour, dows, nm2s = [], {}, {}
        obj1s, obj2s, rucs, anm3s = {}, {}, {}, {}
        for i, dpath in enumerate(prefix_dpaths[prefix]):
            with open(opath.join(dpath, 'res-%s.csv' % prefix)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    date, hour = [row[cn] for cn in ['date', 'hour']]
                    k = (date, hour)
                    if i == 0:
                        dow, numBK, nm2 = [int(row[cn]) for cn in ['dow', 'numBK', 'numMules2']]
                        dateHour.append(k)
                        nm2s[k] = nm2
                        dows[k] = dow
                    #
                    if k not in obj1s:
                        obj1s[k] = []
                        obj2s[k] = []
                        rucs[k] = []
                        anm3s[k] = []
                    obj1, obj2, ruc, anm3 = [float(row[cn]) for cn in
                                                     ['obj1', 'obj2', 'ratioUnCoveredBK', 'actualNumMules3']]
                    obj1s[k].append(obj1)
                    obj2s[k].append(obj2)
                    rucs[k].append(ruc)
                    anm3s[k].append(anm3)
        res_fpath = opath.join('z_data', 'res-%s.csv' % prefix)
        with open(res_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['date', 'dow', 'hour', 'numBK', 'numMules2',
                          'obj1', 'obj2', 'ratioUnCoveredBK', 'actualNumMules3',
                          'min_obj1', 'min_obj2', 'min_ruc', 'min_anm3',
                          'max_obj1', 'max_obj2', 'max_ruc', 'max_anm3',
                          'std_obj1', 'std_obj2', 'std_ruc', 'std_anm3',
                          'data_obj1', 'data_obj2', 'data_ruc', 'data_anm3']
            writer.writerow(new_header)
        for i, (yyyymmdd, hour) in enumerate(dateHour):
            k = (yyyymmdd, hour)
            new_row = [yyyymmdd, dows[k], hour, numBK, nm2s[k]]
            new_row += [np.average(m[k]) for m in [obj1s, obj2s, rucs, anm3s]]
            new_row += [np.min(m[k]) for m in [obj1s, obj2s, rucs, anm3s]]
            new_row += [np.max(m[k]) for m in [obj1s, obj2s, rucs, anm3s]]
            new_row += [np.std(m[k]) for m in [obj1s, obj2s, rucs, anm3s]]
            new_row += [list(m[k]) for m in [obj1s, obj2s, rucs, anm3s]]
            with open(res_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)



if __name__ == '__main__':
    run()