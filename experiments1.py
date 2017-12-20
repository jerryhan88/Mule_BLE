import os.path as opath
import os
import pickle
import random
import datetime
import numpy as np
#
from dataProcessing import *
from problems import *
#
prefix = 'memeticAlgorithm'
pyx_fn, c_fn = '%s.pyx' % prefix, '%s.c' % prefix
if opath.exists(c_fn):
    if opath.getctime(c_fn) < opath.getmtime(pyx_fn):
        from setup import cythonize; cythonize(prefix)
else:
    from setup import cythonize; cythonize(prefix)
from memeticAlgorithm import run as ma_run
from fixedLevel import run as fl_run


def copy_base_inputs(base_inputs):
    inputs = {}
    for k in ['B', 'L', 'e_l', 'K']:
        inputs[k] = base_inputs[k][:]
    inputs['R'] = base_inputs['R']
    return inputs


def get_timeHorizon():
    dt = datetime.datetime(2017, 3, 1)
    firstDOW = dt.weekday()
    timeHorizon = []
    while True:
        dow = dt.weekday()
        if dow in [MON, TUE, WED, THR, FRI]:
            for hour in range(9, 18):
                timeHorizon.append((dt, dow, hour))
        dt += datetime.timedelta(days=1)
        if dt.weekday() == firstDOW:
            break
    return timeHorizon


def get_base_inputs(floor):
    beacon2landmark = get_beacon2landmark(floor)
    bid_index, index_bid = {}, {}
    for i, beaconID in enumerate(beacon2landmark.keys()):
        bid_index[beaconID] = i
        index_bid[i] = beaconID
    B = list(range(len(bid_index)))
    #
    L = list(range(len(PL_RANGE)))
    e_l = PL_CUNSUME
    #
    K = list(range(N_TIMESLOT))
    #
    R = 0.9
    #
    base_inputs = {'B': B,
                   'L': L, 'e_l': e_l,
                   'K': K, 'R': R,
                   'bid_index': bid_index, 'index_bid': index_bid}
    return base_inputs


def get_M_probCov(floor, dow, hour, bid_index):
    mTraj = get_mTraj(floor, dow, hour)
    mid2_index, index_mid2 = {}, {}
    for i, mid in enumerate(mTraj.keys()):
        mid = int(mid[len('m'):])
        mid2_index[mid] = i
        index_mid2[i] = mid
    M = list(range(len(index_mid2)))

    _p_kmbl = get_p_kmbl(floor, dow, hour)
    p_kmbl = {}
    for k, mid, bid, l in _p_kmbl:
        p_kmbl[k, mid2_index[int(mid[len('m'):])], bid_index[bid], l] = _p_kmbl[k, mid, bid, l]
    return M, mid2_index, index_mid2, p_kmbl


def estimation(hour, M3muleLMs, mid_M2M3,
                       base_inputs, plCovLD,
                       index_bid, index_mid2,
                       ls, ms):
    unCoveredBK = set()
    for b in base_inputs['B']:
        for k in base_inputs['K']:
            unCoveredBK.add((b, k))
    selectedMules3 = [mid_M2M3[index_mid2[i]] for i in ms if index_mid2[i] in mid_M2M3]
    coveringBK = set()
    for mid3 in selectedMules3:
        for b, k in unCoveredBK:
            if (hour, k) not in M3muleLMs[mid3]:
                continue
            if set(plCovLD[index_bid[b], ls[b]]).intersection(M3muleLMs[mid3][hour, k]):
                coveringBK.add((b, k))
    unCoveredBK.difference_update(coveringBK)
    #
    return unCoveredBK, selectedMules3


def run_experiments_MA(repeatNum, floor, N_g=300, N_p=50, N_o=40, p_c=0.5, p_m=0.5):
    base_inputs = get_base_inputs(floor)
    bid_index, index_bid = base_inputs['bid_index'], base_inputs['index_bid']
    plCovLD = get_plCovLD(floor)
    numBK = len(base_inputs['B']) * len(base_inputs['K'])
    #
    prefix = '%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' % (floor, N_g, N_p, N_o, p_c, p_m)
    ma_dpath = opath.join('z_data', 'MA-%s-R%d' % (prefix, repeatNum))
    if not opath.exists(ma_dpath):
        os.mkdir(ma_dpath)
    res_fpath = opath.join(ma_dpath, 'res-%s.csv' % prefix)
    with open(res_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['date', 'dow', 'hour', 'numBK', 'numMules2',
                      'obj1', 'obj2', 'ratioUnCoveredBK',
                      'actualNumMules3']
        writer.writerow(new_header)
    #
    timeHorizon = get_timeHorizon()
    c_b = [MAX_BATTERY_POWER for _ in base_inputs['B']]
    dt_muleTraj = {}
    for dt, _, _, in timeHorizon:
        yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
        if dt not in dt_muleTraj:
            dt_muleTraj[dt] = get_M3muleLMs(floor, yyyymmdd)
    while timeHorizon:
        dt, dow, hour = timeHorizon.pop(0)
        yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
        #
        M, mid2_index, index_mid2, p_kmbl = get_M_probCov(floor, dow, hour, bid_index)
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
        #
        # Pickle inputs
        #
        prefix = '%sH%02d' % (yyyymmdd, hour)
        fpath = opath.join(ma_dpath, 'problemInputs-%s.pkl' % prefix)
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
        M3muleLMs, mid_M2M3 = dt_muleTraj[dt]
        unCoveredBK, selectedMules3 = estimation(hour, M3muleLMs, mid_M2M3,
                                                 base_inputs, plCovLD,
                                                 index_bid, index_mid2,
                                                 ls, ms)
        #
        # Logging
        #
        new_row = [yyyymmdd, dow, hour, numBK, len(inputs['M']),
                   obj1, obj2, len(unCoveredBK) / numBK,
                   len(selectedMules3)]
        with open(res_fpath, 'a') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            writer.writerow(new_row)
        #
        c_b = [inputs['c_b'][b] - inputs['e_l'][ls[b]] for b in inputs['B']]


def run_experiments_FL(floor):
    base_inputs = get_base_inputs(floor)
    bid_index, index_bid = base_inputs['bid_index'], base_inputs['index_bid']
    plCovLD = get_plCovLD(floor)
    numBK = len(base_inputs['B']) * len(base_inputs['K'])
    #
    for l in base_inputs['L']:
        res_fpath = opath.join('z_data', 'res-%s-FL%d.csv' % (floor, l))
        with open(res_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['date', 'dow', 'hour', 'numBK', 'numMules2',
                          'obj1', 'obj2', 'ratioUnCoveredBK',
                          'actualNumMules3']
            writer.writerow(new_header)
        #
        timeHorizon = get_timeHorizon()
        c_b = [MAX_BATTERY_POWER for _ in base_inputs['B']]
        dt_muleTraj = {}
        for dt, _, _, in timeHorizon:
            yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
            if dt not in dt_muleTraj:
                dt_muleTraj[dt] = get_M3muleLMs(floor, yyyymmdd)
        while timeHorizon:
            dt, dow, hour = timeHorizon.pop(0)
            yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
            #
            M, mid2_index, index_mid2, p_kmbl = get_M_probCov(floor, dow, hour, bid_index)
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
            M3muleLMs, mid_M2M3 = dt_muleTraj[dt]
            unCoveredBK, selectedMules3 = estimation(hour, M3muleLMs, mid_M2M3,
                                           base_inputs, plCovLD,
                                           index_bid, index_mid2,
                                           ls, ms)
            #
            # Logging
            #
            new_row = [yyyymmdd, dow, hour, numBK, len(inputs['M']),
                       obj1, obj2, len(unCoveredBK) / numBK,
                       len(selectedMules3)]
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
    # run_experiments_MA(0, 'Lv4', N_g=1)
    summary_MA()
