import os.path as opath
import os
import csv, pickle
from functools import reduce
#
from beaconLayout import get_bzDist, get_plCovLD
from beaconLayout import PL_RANGE
from muleTrajectory import mt_dpath


EPOCH_LEAST_RECORDS = 3
#
# Output directory path
#
m1s_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'Markov1Step'])
if not opath.exists(m1s_dpath):
    os.mkdir(m1s_dpath)


def gen_trajCounting(numEpoch=4, month=2):
    ep_dpath = opath.join(m1s_dpath, 'epoch%d' % numEpoch)
    if not opath.exists(ep_dpath):
        os.mkdir(ep_dpath)
    aggTrajCouting_fpath = opath.join(ep_dpath, 'M1SE%d-aggTrajectoryCounting.csv' % numEpoch)
    with open(aggTrajCouting_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['lv', 'month', 'mid',
                      'dow', 'hour', 'epoch',
                      'absent', 'nReocrds', 'nVisitedLocs']
        writer.writerow(new_header)
    #
    muleTraj_fpath = reduce(opath.join,
                     [mt_dpath, 'epoch%d' % numEpoch, 'M2', 'E%d-M2-aggMuleTrajectory.csv' % numEpoch])
    ks = [set() for _ in range(5)]
    trajCouting = {}
    trajCoutingDetail = {}
    with open(muleTraj_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv, mid, dow, hour, epoch = [row[cn] for cn in ['lv', 'mid', 'dow', 'hour', 'epoch']]
            k0 = [lv, mid, dow, hour, epoch]
            for i, ele in enumerate(k0):
                ks[i].add(ele)
            absent = 1 if row['prevHourLoc'] == 'X' else 0
            k1 = tuple(k0 + [absent])
            if k1 not in trajCouting:
                trajCouting[k1] = 0
                trajCoutingDetail[k1] = {}
            trajCouting[k1] += 1
            for loc in eval(row['visitedLocs']):
                if loc not in trajCoutingDetail[k1]:
                    trajCoutingDetail[k1][loc] = 0
                trajCoutingDetail[k1][loc] += 1
    with open(aggTrajCouting_fpath, 'a') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        lvs, mids, dows, hours, epochs = ks
        for lv in lvs:
            for mid in sorted(list(mids)):
                for dow in sorted(list(dows)):
                    for hour in sorted(list(hours)):
                        for epoch in sorted(list(epochs)):
                            k0 = (lv, mid, dow, hour, epoch, 0)
                            k1 = (lv, mid, dow, hour, epoch, 1)
                            if k0 in trajCouting and k1 in trajCouting:
                                if trajCouting[k0] + trajCouting[k1] < EPOCH_LEAST_RECORDS:
                                    continue
                                writer.writerow([lv, month, mid,
                                                 dow, hour, epoch,
                                                 0, trajCouting[k0], trajCoutingDetail[k0]])
                                writer.writerow([lv, month, mid,
                                                 dow, hour, epoch,
                                                 1, trajCouting[k1], trajCoutingDetail[k1]])
                            else:
                                if k0 in trajCouting:
                                    assert k1 not in trajCouting
                                    if trajCouting[k0] < EPOCH_LEAST_RECORDS:
                                        continue
                                    writer.writerow([lv, month, mid,
                                                     dow, hour, epoch,
                                                     0, trajCouting[k0], trajCoutingDetail[k0]])
                                elif k1 in trajCouting:
                                    assert k0 not in trajCouting
                                    if trajCouting[k1] < EPOCH_LEAST_RECORDS:
                                        continue
                                    writer.writerow([lv, month, mid,
                                                     dow, hour, epoch,
                                                     1, trajCouting[k1], trajCoutingDetail[k1]])


def gen_p_kmbl(numEpoch=4):
    ep_dpath = opath.join(m1s_dpath, 'epoch%d' % numEpoch)
    aggTrajCouting_fpath = opath.join(ep_dpath, 'M1SE%d-aggTrajectoryCounting.csv' % numEpoch)
    bids, plCovLD = {}, {}
    with open(aggTrajCouting_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv = row['lv']
            lv_dpath = opath.join(ep_dpath, lv)
            p_dpath = opath.join(lv_dpath, 'p_kmbl')
            for dpath in [lv_dpath, p_dpath]:
                if not opath.exists(dpath):
                    os.mkdir(dpath)
            mid = row['mid']
            _mid = 'm%s' % mid
            ofpath = opath.join(p_dpath, 'M1SE%d-%s-p-%s.csv' % (numEpoch, lv, _mid))
            if not opath.exists(ofpath):
                with open(ofpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_header = ['lv', 'mid', 'dow', 'hour', 'epoch', 'absent',
                                  'bid', 'pl', 'p_kmbl',
                                  'nReocrds', 'withinLocs']
                    writer.writerow(new_header)
            if lv not in bids:
                bzDist = get_bzDist(lv)
                bids[lv] = list(bzDist.keys())
                plCovLD[lv] = get_plCovLD(lv)
            #
            dow, hour, epoch, absent = [row[cn] for cn in ['dow', 'hour', 'epoch', 'absent']]
            nReocrds, nVisitedLocs = [eval(row[cn]) for cn in ['nReocrds', 'nVisitedLocs']]
            for bid, bidLong in enumerate(bids[lv]):
                for pl in range(len(PL_RANGE)):
                    visitedLocs = set(nVisitedLocs.keys())
                    coveringLD = set(plCovLD[lv][bidLong, pl])
                    intersectLocs = visitedLocs.intersection(coveringLD)
                    if intersectLocs:
                        _p_kmbl = 1
                        for loc in intersectLocs:
                            _p_kmbl *= (1 - (int(nVisitedLocs[loc]) / float(nReocrds)))
                            if _p_kmbl == 0.0:
                                break
                        p_kmbl = 1 - _p_kmbl
                    else:
                        p_kmbl = 0.0
                    new_row = [lv, mid, dow, hour, epoch, absent,
                               bid, pl, p_kmbl, nReocrds, dict((loc, nVisitedLocs[loc]) for loc in intersectLocs)]
                    with open(ofpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow(new_row)


def arrange_p_kmbl(numEpoch=4):
    ep_dpath = opath.join(m1s_dpath, 'epoch%d' % numEpoch)
    for lv in os.listdir(ep_dpath):
        if not opath.isdir(opath.join(ep_dpath, lv)):
            continue
        lv_dpath = opath.join(ep_dpath, lv)
        p0_dpath = opath.join(lv_dpath, 'p_kmbl')
        p1_dpath = opath.join(lv_dpath, 'arr_p_kmbl')
        if not opath.exists(p1_dpath):
            os.mkdir(p1_dpath)
        dh_mules, dh_p_kmbl = {}, {}
        for fn in os.listdir(p0_dpath):
            if not fn.endswith('.csv'):
                continue
            with open(opath.join(p0_dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    dow, hour = [int(row[cn]) for cn in ['dow', 'hour']]
                    fpath = opath.join(p1_dpath, 'M1SE%d-W%d-H%02d.csv' % (numEpoch, dow, hour))
                    if not opath.exists(fpath):
                        with open(fpath, 'w') as w_csvfile:
                            writer = csv.writer(w_csvfile, lineterminator='\n')
                            new_header = ['lv', 'dow', 'hour', 'absent', 'epoch', 'mid', 'bid', 'pl', 'p_kmbl']
                            writer.writerow(new_header)
                    absent, epoch, mid, bid, pl = [row[cn] for cn in ['absent', 'epoch', 'mid', 'bid', 'pl']]
                    p_kmbl = eval(row['p_kmbl'])
                    if (dow, hour) not in dh_mules:
                        dh_mules[dow, hour] = set()
                        dh_p_kmbl[dow, hour] = {}
                    dh_mules[dow, hour].add(mid)
                    dh_p_kmbl[dow, hour][absent, epoch, mid, bid, pl] = p_kmbl
                    #
                    new_row = [lv, dow, hour, absent, epoch, mid, bid, pl, p_kmbl]
                    with open(fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow(new_row)
        dh_mules_fpath = opath.join(lv_dpath, '_M1SE%d-%s-muleDH.csv' % (numEpoch, lv))
        with open(dh_mules_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['dow', 'hour', 'numMules', 'mules']
            writer.writerow(new_header)
            for dow, hour in dh_mules:
                writer.writerow([dow, hour, len(dh_mules[dow, hour]), list(dh_mules[dow, hour])])
        p_kmbl_fpath = opath.join(lv_dpath, '_M1SE%d-%s-p_kmbl.pkl' % (numEpoch, lv))
        with open(p_kmbl_fpath, 'wb') as fp:
            pickle.dump(dh_p_kmbl, fp)


if __name__ == '__main__':
    gen_trajCounting(numEpoch=1, month=2)
    gen_p_kmbl(numEpoch=1)
    arrange_p_kmbl(numEpoch=1)
