import os.path as opath
import os
import csv, pickle
import random
import datetime
import numpy as np
from functools import reduce
#
from a1_muleDuration import md_dpath
from Markov1Step import m1s_dpath
from muleDayTrajecty import mdt_dpath
from beaconLayout import get_bzDist, get_plCovLD
from a1_muleDuration import MON, TUE, WED, THR, FRI
from beaconLayout import PL_RANGE, TARGET_LVS
#
# from problems import *
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


PL_CUNSUME = [1, 6.3095734447, 15.8489319246]
MIN_BATTERY_POWER, MAX_BATTERY_POWER = 980, 1000
SCANNING_ENERGY = 0.01


exp_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'experiments'])
if not opath.exists(exp_dpath):
    os.mkdir(exp_dpath)


def get_timeHorizon():
    dt = datetime.datetime(2017, 3, 1)
    firstDOW = dt.weekday()
    timeHorizon = []
    while True:
        dow = dt.weekday()
        if dow in [MON, TUE, WED, THR, FRI]:
            for hour in range(9, 18):
                dt = datetime.datetime(dt.year, dt.month, dt.day, hour)
                timeHorizon.append(dt)
        dt += datetime.timedelta(days=1)
        if dt.weekday() == firstDOW:
            break
    return timeHorizon


def init_experiments(numEpoch=4):
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
        K = list(range(numEpoch))
        #
        R = 0.9
        #
        base_inputs = {'B': B, 'c_b': c_b,
                       'L': L, 'e_l': e_l,
                       'K': K, 'R': R, 'bidConverter': bid_bidLong}
        return base_inputs
    #
    ep_dpath = opath.join(exp_dpath, 'epoch%d' % numEpoch)
    if not opath.exists(ep_dpath):
        os.mkdir(ep_dpath)
    __mid_madd = []
    for month in range(2, 4):
        muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % month, '_muleID-M%d.pkl' % month])
        with open(muleID_fpath, 'rb') as fp:
            _, mid_madd = pickle.load(fp)
            __mid_madd.append(mid_madd)
    mid_madd2, mid_madd3 = __mid_madd
    #
    timeHorizon = get_timeHorizon()
    for lv in TARGET_LVS:
        dh_madd_ab_p_kbl = {}
        lv_dpath = opath.join(ep_dpath, lv)
        if not opath.exists(lv_dpath):
            os.mkdir(lv_dpath)
        inputs_dpath = opath.join(lv_dpath, 'inputs')
        bi_fpath = opath.join(inputs_dpath, 'base_input.pkl')
        p_dpath = opath.join(inputs_dpath, 'p_kmbl')
        for dpath in [inputs_dpath, p_dpath]:
            if not opath.exists(dpath):
                os.mkdir(dpath)
        base_inputs = get_base_inputs(lv)
        with open(bi_fpath, 'wb') as fp:
            pickle.dump(base_inputs, fp)
        epochs, bids, pls = set(), set(), set()
        for dt in timeHorizon:
            dh = (dt.weekday(), dt.hour)
            if dh not in dh_madd_ab_p_kbl:
                dh_madd_ab_p_kbl[dh] = {}
                m2_p_fpath = reduce(opath.join, [m1s_dpath, 'epoch%d' % numEpoch, lv, 'arr_p_kmbl',
                                    'M1SE%d-W%d-H%02d.csv' % (numEpoch, dt.weekday(), dt.hour)])
                with open(m2_p_fpath) as r_csvfile:
                    reader = csv.DictReader(r_csvfile)
                    for row in reader:
                        mid0 = int(row['mid'])
                        madd = mid_madd2[mid0]
                        if madd not in dh_madd_ab_p_kbl[dh]:
                            dh_madd_ab_p_kbl[dh][madd] = {}
                        absent, epoch, bid, pl = [int(row[cn]) for cn in ['absent', 'epoch', 'bid', 'pl']]
                        if absent not in dh_madd_ab_p_kbl[dh][madd]:
                            dh_madd_ab_p_kbl[dh][madd][absent] = {}
                        dh_madd_ab_p_kbl[dh][madd][absent][epoch, bid, pl] = eval(row['p_kmbl'])
                        epochs.add(epoch)
                        bids.add(bid)
                        pls.add(pl)
            #
            m3_p_fpath = opath.join(p_dpath, 'E%d-p-%02d%02d-H%02d.csv' % (numEpoch, dt.month, dt.day, dt.hour))
            with open(m3_p_fpath, 'w') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                new_header = ['day', 'dow', 'hour', 'epoch', 'mid', 'bid', 'pl', 'p_kmbl']
                writer.writerow(new_header)
            #
            madd_ab_p_kbl = dh_madd_ab_p_kbl[dh]
            mdt_fpath = reduce(opath.join, [mdt_dpath, 'epoch%d' % numEpoch, lv,
                        'mdt-%s-%02d%02d-H%02d-W%d.csv' % (lv, dt.month, dt.day, dt.hour, dt.weekday())])
            mid0_mid1 = {}
            with open(mdt_fpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    mid0 = int(row['mid'])
                    if mid0 not in mid0_mid1:
                        mid0_mid1[mid0] = len(mid0_mid1)
                    mid1 = mid0_mid1[mid0]
                    if mid_madd3[mid0] not in madd_ab_p_kbl:
                        p_kmbl = 0.0
                        for k in epochs:
                            for bid in bids:
                                for pl in pls:
                                    with open(m3_p_fpath, 'a') as w_csvfile:
                                        writer = csv.writer(w_csvfile, lineterminator='\n')
                                        new_row = [dt.day, dt.weekday(), dt.hour,
                                                   k, mid1, bid, pl, p_kmbl]
                                        writer.writerow(new_row)
                    else:
                        madd = mid_madd3[mid0]
                        absent = int(row['absent'])
                        for k in epochs:
                            for bid in bids:
                                for pl in pls:
                                    if absent not in madd_ab_p_kbl[madd]:
                                        p_kmbl = 0.0
                                    else:
                                        if (epoch, bid, pl) not in madd_ab_p_kbl[madd][absent]:
                                            p_kmbl = 0.0
                                        else:
                                            p_kmbl = madd_ab_p_kbl[madd][absent][epoch, bid, pl]
                                    with open(m3_p_fpath, 'a') as w_csvfile:
                                        writer = csv.writer(w_csvfile, lineterminator='\n')
                                        new_row = [dt.day, dt.weekday(), dt.hour,
                                                   k, mid1, bid, pl, p_kmbl]
                                        writer.writerow(new_row)


def copy_base_inputs(base_inputs):
    inputs = {}
    for k in ['B', 'L', 'e_l', 'K']:
        inputs[k] = base_inputs[k][:]
    inputs['R'] = base_inputs['R']
    return inputs


def get_M_probCov(numEpoch, lv, dt):
    p_fpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'inputs', 'p_kmbl',
              'E%d-p-%02d%02d-H%02d.csv' % (numEpoch, dt.month, dt.day, dt.hour)])
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


def estimation(dt, lv, base_inputs, ls, ms, plCovLD, numEpoch=4):
    epochVisitedLocs = {}
    mdt_fpath = reduce(opath.join, [mdt_dpath, 'epoch%d' % numEpoch, lv,
                                    'mdt-%s-%02d%02d-H%02d-W%d.csv' % (lv, dt.month, dt.day, dt.hour, dt.weekday())])
    mid0_mid1 = {}
    with open(mdt_fpath) as r_csvfile:
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


def run_experiments_MA(repeatNum, numEpoch, lv,
                       N_g=300, N_p=50, N_o=40, p_c=0.5, p_m=0.5, N_s=10,
                       randomSolCoice=True):
    res_dpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'results'])
    if not opath.exists(res_dpath):
        os.mkdir(res_dpath)
    prefix = 'G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' % (N_g, N_p, N_o, p_c, p_m)
    ma_dpath = opath.join(res_dpath, 'MA%d-%s-R%d' % (int(randomSolCoice), prefix, repeatNum))
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
    bi_fpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'inputs', 'base_input.pkl'])
    with open(bi_fpath, 'rb') as fp:
        base_inputs = pickle.load(fp)
    plCovLD = get_plCovLD(lv)
    numBK = len(base_inputs['B']) * len(base_inputs['K'])
    c_b = [MAX_BATTERY_POWER for _ in base_inputs['B']]
    while timeHorizon:
        dt = timeHorizon.pop(0)
        yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
        #
        M, p_kmbl = get_M_probCov(numEpoch, lv, dt)
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
        if randomSolCoice:
            ind = random.choice(list(paretoFront.values()))
        else:
            minMule, mmInd = 1e400, None
            for (_, obj2), candiIndi in paretoFront.items():
                if obj2 < minMule:
                    minMule, mmInd = obj2, candiIndi
            ind = mmInd
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
        # c_b = [inputs['c_b'][b] - inputs['e_l'][ls[b]] - SCANNING_ENERGY for b in inputs['B']]
        c_b = [inputs['c_b'][b] - inputs['e_l'][ls[b]] for b in inputs['B']]


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


def summary_MA(numEpoch=4, lv='Lv4', randomSolCoice=False):
    res_dpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'results'])
    prefix_dpaths = {}
    for dn in os.listdir(res_dpath):
        if not dn.startswith('MA%d' % int(randomSolCoice)):
            continue
        _, _, _, _, _, _, _repeatNum = dn.split('-')
        prefix = dn[len('MA0-'):-len('-%s' % _repeatNum)]
        if prefix not in prefix_dpaths:
            prefix_dpaths[prefix] = []
        prefix_dpaths[prefix].append(opath.join(res_dpath, dn))
    for prefix in prefix_dpaths:
        numBK = None
        dateHour, dows, nms = [], {}, {}
        obj1s, obj2s, rucs = {}, {}, {}
        for i, dpath in enumerate(prefix_dpaths[prefix]):
            with open(opath.join(dpath, 'res-%s.csv' % prefix)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    date, hour = [row[cn] for cn in ['date', 'hour']]
                    k = (date, hour)
                    if i == 0:
                        dow, numBK, nm = [int(row[cn]) for cn in ['dow', 'numBK', 'numMules']]
                        dateHour.append(k)
                        dows[k] = dow
                        nms[k] = nm
                    #
                    if k not in obj1s:
                        obj1s[k] = []
                        obj2s[k] = []
                        rucs[k] = []
                    obj1, obj2, ruc = [float(row[cn]) for cn in
                                                     ['obj1', 'obj2', 'ratioUnCoveredBK']]
                    obj1s[k].append(obj1)
                    obj2s[k].append(obj2)
                    rucs[k].append(ruc)
        res_fpath = opath.join(res_dpath, 'E%d-res-MA%d-%s.csv' % (numEpoch, int(randomSolCoice), prefix))
        with open(res_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['date', 'dow', 'hour', 'numBK', 'numMules',
                          'obj1', 'obj2', 'ratioUnCoveredBK',
                          'min_obj1', 'min_obj2', 'min_ratioUnCoveredBK',
                          'max_obj1', 'max_obj2', 'max_ratioUnCoveredBK',
                          'std_obj1', 'std_obj2', 'std_ratioUnCoveredBK',
                          'data_obj1', 'data_obj2', 'data_ratioUnCoveredBK']
            writer.writerow(new_header)
        for i, (yyyymmdd, hour) in enumerate(dateHour):
            k = (yyyymmdd, hour)
            new_row = [yyyymmdd, dows[k], hour, numBK, nms[k]]
            new_row += [np.average(m[k]) for m in [obj1s, obj2s, rucs]]
            new_row += [np.min(m[k]) for m in [obj1s, obj2s, rucs]]
            new_row += [np.max(m[k]) for m in [obj1s, obj2s, rucs]]
            new_row += [np.std(m[k]) for m in [obj1s, obj2s, rucs]]
            new_row += [list(m[k]) for m in [obj1s, obj2s, rucs]]
            with open(res_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)

# import pandas as pd
#
# def comp_epochs():
#     lv = 'Lv4'
#     prefix = 'G(50)-P(100)-O(80)-pC(0.50)-pM(0.50)'
#     ce_fpath = 'epochComparision.csv'
#     with open(ce_fpath, 'w') as w_csvfile:
#         writer = csv.writer(w_csvfile, lineterminator='\n')
#         new_header = ['numEpoch',
#                       'obj1', 'obj2', 'ratioUnCoveredBK']
#         writer.writerow(new_header)
#     for numEpoch in [1, 2, 4]:
#         res_dpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'results'])
#         res_fpath = opath.join(res_dpath, 'E%d-res-MA1-%s.csv' % (numEpoch, prefix))
#
#         pd.read_csv(res_fpath)
#
#
#         print(res_fpath)


if __name__ == '__main__':
    # init_experiments(numEpoch=1)
    #
    # run_experiments_MA(0, 2, 'Lv4', N_g=50, N_p=100, N_o=80, p_c=0.5, p_m=0.5, randomSolCoice=True)
    summary_MA(numEpoch=2, lv='Lv4', randomSolCoice=False)
    # comp_epochs()
