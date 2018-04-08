import os.path as opath
import os
import pickle
import time
import numpy as np
import csv
#

prefix = 'memeticAlgorithm'
pyx_fn, c_fn = '%s.pyx' % prefix, '%s.c' % prefix
if opath.exists(c_fn):
    if opath.getctime(c_fn) < opath.getmtime(pyx_fn):
        from setup import cythonize; cythonize(prefix)
else:
    from setup import cythonize; cythonize(prefix)
from memeticAlgorithm import run as ma_run


# prefix = '_MA-Lv4-G(50)-P(50)-O(40)-pC(0.50)-pM(0.50)-R0'


dpath = opath.join('z_data', 'experiment2')
fn = 'problemInputs-20170306H11.pkl'
ifpath = opath.join(dpath, fn)
with open(ifpath, 'rb') as fp:
    inputs = pickle.load(fp)


# '20170306	0	11	numMules 55'

N_p, N_o, p_c, p_m = 50, 40, 0.5, 0.5


def run(repeatNum, N_g, sampling=True):
    fpath = opath.join(dpath, 'G%d-S%d-R%d.csv' % (N_g, sampling, repeatNum))
    #
    numNeighbors = (len(inputs['L']) - 1) * len(inputs['B']) + len(inputs['M'])
    if sampling:
        N_s = int(numNeighbors * 0.2)
    else:
        N_s = numNeighbors

    print('B', len(inputs['B']))
    print('M', len(inputs['M']))
    print(N_s, (len(inputs['L']) - 1) * len(inputs['B']), len(inputs['M']))

    assert False

    inputs['N_g'] = N_g
    inputs['N_p'] = N_p
    inputs['N_o'] = N_o
    inputs['p_c'] = p_c
    inputs['p_m'] = p_m
    inputs['N_s'] = N_s
    oldTime = time.time()
    paretoFront, evolution = ma_run(inputs)

    obj1s, obj2s = [], []
    for (obj1, obj2) in paretoFront:
        obj1s.append(obj1)
        obj2s.append(obj2)
    with open(fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        header = ['obj1', 'obj2', 'comTime']
        writer.writerow(header)
        writer.writerow([np.average(obj1s), np.average(obj2s), time.time() - oldTime])



def summary():
    GS_fns = {}
    for fn in os.listdir(dpath):
        if not fn.startswith('G'):
            continue
        assert fn.endswith('.csv')
        G, S, _ = fn[:-len('.csv')].split('-')
        if (G, S) not in GS_fns:
            GS_fns[G, S] = []
        GS_fns[G, S].append(fn)
    #
    for G, S in GS_fns:
        fpath = opath.join(dpath, 'summary-%s-%s.csv' % (G, S))
        with open(fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            header = ['obj1', 'obj2', 'comTime']
            writer.writerow(header)
        #
        for fn in GS_fns[G, S]:
            with open(opath.join(dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    with open(fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow([row[cn] for cn in ['obj1', 'obj2', 'comTime']])




if __name__ == '__main__':
    run(1000, 50, sampling=False)
    # summary()