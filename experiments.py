import os.path as opath
import os
import pickle
import random
import datetime
import numpy as np
from functools import reduce
#
from dataProcessing import *
from problems import *
#
# prefix = 'memeticAlgorithm'
# pyx_fn, c_fn = '%s.pyx' % prefix, '%s.c' % prefix
# if opath.exists(c_fn):
#     if opath.getctime(c_fn) < opath.getmtime(pyx_fn):
#         from setup import cythonize; cythonize(prefix)
# else:
#     from setup import cythonize; cythonize(prefix)
from memeticAlgorithm import run as ma_run
from fixedLevel import run as fl_run


SCANNING_ENERGY = 0.01


def copy_base_inputs(base_inputs):
    inputs = {}
    for k in ['B', 'L', 'e_l', 'K']:
        inputs[k] = base_inputs[k][:]
    inputs['R'] = base_inputs['R']
    return inputs


def get_base_inputs(lv):
    bid_bidLong = {}
    for bid, bidLong in enumerate(get_bzDist(lv)):
        bid_bidLong[bid] = bidLong
    B = list(range(len(bid_bidLong)))
    c_b = [MAX_BATTERY_POWER for _ in B]
    #
    L = list(range(len(PL_RANGE)))
    e_l = PL_CUNSUME
    #
    K = list(range(N_TIMESLOT))
    #
    R = 0.9
    #
    base_inputs = {'B': B, 'c_b': c_b,
                   'L': L, 'e_l': e_l,
                   'K': K, 'R': R, 'bidConverter': bid_bidLong}
    return base_inputs


def get_M_probCov(lv, dt):
    p_dpath = reduce(opath.join, ['z_data', '_experiments', lv, 'p_kmbl'])
    p_fpath = opath.join(p_dpath, 'p_kmbl-%02d%02d-H%02d.csv' % (dt.month, dt.day, dt.hour))
    #
    mids, p_kmbl = set(), {}
    with open(p_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            epoch, mid, bid, pl = [int(row[cn]) for cn in ['epoch', 'mid', 'bid', 'pl']]
            mids.add(mid)
            p_kmbl[epoch, mid, bid, pl] = eval(row['p_kmbl'])
    M = list(mids)
    return M, p_kmbl


def estimation(dt, lv, base_inputs, ls, ms, plCovLD):
    epochVisitedLocs = {}
    trajByDay_fpath = reduce(opath.join, [get_base_dpath(dt.month), 'M%d-%s' % (dt.month, lv),
                                          'trajByDay',
                                          '%02d%02d-H%02d-W%d.csv' % (dt.month, dt.day, dt.hour, dt.weekday())])
    mid0_mid1 = {}
    with open(trajByDay_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            mid0, epoch = [int(row[cn]) for cn in ['mid', 'epoch']]
            if mid0 not in mid0_mid1:
                mid0_mid1[mid0] = len(mid0_mid1)
            mid1 = mid0_mid1[mid0]
            if mid1 in ms:
                if epoch not in epochVisitedLocs:
                    epochVisitedLocs[epoch] = set()
                for loc in eval(row['visitedLocs']):
                    epochVisitedLocs[epoch].add(loc)
    #
    unCoveredBK = set()
    for b in base_inputs['B']:
        for k in base_inputs['K']:
            unCoveredBK.add((b, k))
    coveringBK = set()
    for b, k in unCoveredBK:
        if k not in epochVisitedLocs:
            continue
        if set(plCovLD[base_inputs['bidConverter'][b], ls[b]]).intersection(epochVisitedLocs[k]):
            coveringBK.add((b, k))
    #
    return unCoveredBK.difference(coveringBK)


def run_experiments_MA(repeatNum, lv, N_g=300, N_p=50, N_o=40, p_c=0.5, p_m=0.5, N_s=10):
    prefix = 'G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' % (N_g, N_p, N_o, p_c, p_m)
    ma_dpath = reduce(opath.join, ['z_data', '_experiments', lv,
                                   'MA-%s-R%d' % (prefix, repeatNum)])
    if not opath.exists(ma_dpath):
        os.mkdir(ma_dpath)
    input_pkl_dpath = opath.join(ma_dpath, 'inputs')
    if not opath.exists(input_pkl_dpath):
        os.mkdir(input_pkl_dpath)
    res_fpath = opath.join(ma_dpath, 'res-%s.csv' % prefix)
    with open(res_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['date', 'dow', 'hour', 'numBK', 'numMules',
                      'obj1', 'obj2', 'ratioUnCoveredBK']
        writer.writerow(new_header)
    #
    timeHorizon = get_timeHorizon()
    base_inputs = get_base_inputs(lv)
    plCovLD = get_plCovLD(lv)
    numBK = len(base_inputs['B']) * len(base_inputs['K'])
    c_b = [MAX_BATTERY_POWER for _ in base_inputs['B']]
    while timeHorizon:
        dt = timeHorizon.pop(0)
        yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
        #
        M, p_kmbl = get_M_probCov(lv, dt)
        #
        inputs = copy_base_inputs(base_inputs)
        inputs['M'] = M
        inputs['p_kmbl'] = p_kmbl
        inputs['c_b'] = c_b
        #
        inputs['N_g'] = N_g
        inputs['N_p'] = N_p
        inputs['N_o'] = N_o
        inputs['p_c'] = p_c
        inputs['p_m'] = p_m
        inputs['N_s'] = N_s
        #
        # Pickle inputs
        #
        prefix = '%sH%02d' % (yyyymmdd, dt.hour)
        fpath = opath.join(input_pkl_dpath, 'inputs-%s.pkl' % prefix)
        with open(fpath, 'wb') as fp:
            pickle.dump(inputs, fp)
        #
        paretoFront, evolution = ma_run(inputs)
        #
        # Record evolution
        #
        evol_fpath = opath.join(ma_dpath, 'evol-%s.csv' % prefix)
        with open(evol_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['generation', 'paretoFront']
            writer.writerow(new_header)
        for i, objs in enumerate(evolution):
            objs = list(objs)
            objs.sort()
            new_row = [i + 1, objs]
            with open(evol_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)
        #
        ind = random.choice(list(paretoFront.values()))
        obj1, obj2 = ind.obj1, ind.obj2
        ls = ind.g1[:]
        ms = [i for i, y_m in enumerate(ind.g2) if y_m == 1]
        #
        # Estimate the ratio of uncovered BK pairs and logging
        #
        unCoveredBK = estimation(dt, lv, base_inputs, ls, ms, plCovLD)
        #
        # Logging
        #
        new_row = [yyyymmdd, dt.weekday(), dt.hour, numBK, len(inputs['M']),
                   obj1, obj2, len(unCoveredBK) / numBK]
        with open(res_fpath, 'a') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            writer.writerow(new_row)
        #
        c_b = [inputs['c_b'][b] - inputs['e_l'][ls[b]] - SCANNING_ENERGY for b in inputs['B']]


def run_experiments_FL(lv):
    base_inputs = get_base_inputs(lv)
    plCovLD = get_plCovLD(lv)
    numBK = len(base_inputs['B']) * len(base_inputs['K'])
    #
    for l in base_inputs['L']:
        fl_dpath = reduce(opath.join, ['z_data', '_experiments', lv, 'FL'])
        if not opath.exists(fl_dpath):
            os.mkdir(fl_dpath)
        res_fpath = opath.join(fl_dpath, 'res-FL%d.csv' % (l))
        with open(res_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['date', 'dow', 'hour', 'numBK', 'numMules',
                          'obj1', 'obj2', 'ratioUnCoveredBK']
            writer.writerow(new_header)
        #
        timeHorizon = get_timeHorizon()
        c_b = [MAX_BATTERY_POWER for _ in base_inputs['B']]
        while timeHorizon:
            dt = timeHorizon.pop(0)
            yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
            #
            M, p_kmbl = get_M_probCov(lv, dt)
            #
            inputs = copy_base_inputs(base_inputs)
            inputs['M'] = M
            inputs['p_kmbl'] = p_kmbl
            inputs['c_b'] = c_b
            inputs['FL'] = l
            obj1, obj2, ls, ms = fl_run(inputs)
            #
            # Estimate the ratio of uncovered BK pairs and logging
            #
            unCoveredBK = estimation(dt, lv, base_inputs, ls, ms, plCovLD)
            #
            # Logging
            #
            new_row = [yyyymmdd, dt.weekday(), dt.hour, numBK, len(inputs['M']),
                       obj1, obj2, len(unCoveredBK) / numBK]
            with open(res_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)
            #
            c_b = [inputs['c_b'][b] - inputs['e_l'][ls[b]] for b in inputs['B']]


def summary_MA():
    prefix_dpaths = {}
    for dn in os.listdir('z_data'):
        if not dn.startswith('_'):
            continue
        _, _, _, _, _, _, _, _repeatNum = dn.split('-')

        prefix = dn[len('_MA-'):-len('-%s' % _repeatNum)]
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
                          'min_obj1', 'min_obj2', 'min_ratioUnCoveredBK', 'min_anm3',
                          'max_obj1', 'max_obj2', 'max_ratioUnCoveredBK', 'max_anm3',
                          'std_obj1', 'std_obj2', 'std_ratioUnCoveredBK', 'std_anm3',
                          'data_obj1', 'data_obj2', 'data_ratioUnCoveredBK', 'data_anm3']
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
    # run_experiments_FL('Lv4')
    # import time
    # oldTime = time.time()
    run_experiments_MA(1000, 'Lv2', N_g=50)
    # print(time.time() - oldTime)
    # summary_MA()
