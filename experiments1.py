import os.path as opath
import os
import pickle
import random
import datetime
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


floor = 'Lv2'
numGeneration = 300
numPopulation = 50
numOffsprings = int(numPopulation * 0.8)
probCrossover = 0.5
probMutation = 0.5

maProb_dpath = opath.join('z_data', 'maRes-%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' %
                          (floor, numGeneration, numPopulation, numOffsprings, probCrossover, probMutation))
if not opath.exists(maProb_dpath):
    os.mkdir(maProb_dpath)


def copy_base_inputs(base_inputs):
    inputs = {}
    for k in ['B', 'L', 'e_l', 'K']:
        inputs[k] = base_inputs[k][:]
    inputs['R'] = base_inputs['R']
    return inputs


def run_fixedPL0(dow, hour, etc):
    base_inputs = etc['base_inputs']
    B, L = [base_inputs.get(k) for k in ['B', 'L']]
    pl = [L[0] for _ in B]
    return pl


def run_fixedPL1(dow, hour, etc):
    base_inputs = etc['base_inputs']
    B, L = [base_inputs.get(k) for k in ['B', 'L']]
    pl = [L[1] for _ in B]
    return pl


def run_fixedPL2(dow, hour, etc):
    base_inputs = etc['base_inputs']
    B, L = [base_inputs.get(k) for k in ['B', 'L']]
    pl = [L[2] for _ in B]
    return pl


def run_memeticAlgorithm(dow, hour, etc):
    base_inputs, bid_index, c_b = [etc.get(k) for k in ['base_inputs', 'bid_index', 'c_b']]
    #
    mTraj = get_mTraj(floor, dow, hour)
    mid_index = {}
    for i, mid in enumerate(mTraj.keys()):
        mid_index[mid] = i
    M = list(range(len(mid_index)))
    #
    _p_kmbl = get_p_kmbl(floor, dow, hour)
    p_kmbl = {}
    for k, mid, bid, l in _p_kmbl:
        p_kmbl[k, mid_index[mid], bid_index[bid], l] = _p_kmbl[k, mid, bid, l]
    #
    inputs = copy_base_inputs(base_inputs)
    inputs['M'] = M
    inputs['p_kmbl'] = p_kmbl
    inputs['c_b'] = c_b
    paretoFront = ma_run(inputs,
                         numGeneration, numPopulation, numOffsprings, probCrossover, probMutation)
    #
    ind = random.choice(list(paretoFront.values()))
    pl = ind.g1
    #
    fpath = opath.join(maProb_dpath, '%sH%02d.pkl' % (etc['date'], hour))
    with open(fpath, 'wb') as fp:
        pickle.dump([inputs, bid_index], fp)
    return pl


def run(appName='MA'):
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
    appraches = {'MA': run_memeticAlgorithm,
                 'FL0': run_fixedPL0,
                 'FL1': run_fixedPL1,
                 'FL2': run_fixedPL2}
    #
    if appName == 'MA':
        fpath = opath.join('z_data', 'res-%s-%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f).csv' %
                           (floor, appName, numGeneration, numPopulation, numOffsprings, probCrossover, probMutation))
        pass
    else:
        fpath = opath.join('z_data', 'res-%s-%s.csv' % (floor, appName))
    approach_run = appraches[appName]
    with open(fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['date', 'dow', 'hour', 'obj1', 'obj2', 'numUnCoveredBK', 'unCoveredBK', 'numWholeMules']
        writer.writerow(new_header)
    #
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
                   'K': K, 'R': R}
    #
    plCovLD = get_plCovLD(floor)
    timeHorizon = get_timeHorizon()
    c_b = [MAX_BATTERY_POWER for _ in B]
    dt_muleTraj = {}
    while timeHorizon:
        dt, dow, hour = timeHorizon.pop(0)
        yyyymmdd = '2017%02d%02d' % (dt.month, dt.day)
        etc = {'base_inputs': base_inputs,
               'bid_index': bid_index,
               'c_b': c_b,
               'date': yyyymmdd}
        pl = approach_run(dow, hour, etc)
        #
        # Estimate the number of mules
        #
        if dt not in dt_muleTraj:
            dt_muleTraj[dt] = get_M3muleLMs(floor, yyyymmdd)
        M3muleLMs = dt_muleTraj[dt]
        unCoveredBK = set()
        for b in B:
            for k in K:
                unCoveredBK.add((b, k))
        selectedMules =set()
        is_feasible = True
        while True:
            alpha_mule, muleCoveringBK, max_numCovering = None, None, -1e400
            for mid in M3muleLMs:
                if mid in selectedMules:
                    continue
                coveringBK = set()
                for b, k in unCoveredBK:
                    if (hour, k) not in M3muleLMs[mid]:
                        continue
                    if set(plCovLD[index_bid[b], pl[b]]).intersection(M3muleLMs[mid][hour, k]):
                        coveringBK.add((b, k))
                if max_numCovering < len(coveringBK):
                    alpha_mule = mid
                    muleCoveringBK = coveringBK
                    max_numCovering = len(coveringBK)
            if alpha_mule is None:
                is_feasible = False
                break
            selectedMules.add(alpha_mule)
            unCoveredBK.difference_update(muleCoveringBK)
            if not unCoveredBK:
                break
        obj2 = len(selectedMules)
        #
        # Estimate the remaining battery capacity
        #
        new_c_b = []
        for b in B:
            new_c_b.append(c_b[b] - e_l[pl[b]])
        obj1 = min(new_c_b)
        #
        # Logging
        #
        wholeMules = set()
        for mid in M3muleLMs:
            for k in K:
                if (hour, k) not in M3muleLMs[mid]:
                    continue
                wholeMules.add(mid)
        new_row = [yyyymmdd, dow, hour, obj1]
        if is_feasible:
            new_row += [obj2, None, None, len(wholeMules)]
        else:
            new_row += [len(wholeMules), len(unCoveredBK), list(unCoveredBK), len(wholeMules)]
        with open(fpath, 'a') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            writer.writerow(new_row)
        #
        c_b = new_c_b


if __name__ == '__main__':
    run('MA')