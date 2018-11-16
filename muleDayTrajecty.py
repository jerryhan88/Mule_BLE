import os.path as opath
import os
import csv, pickle
from functools import reduce
#
from beaconLayout import TARGET_LVS
from a1_muleDuration import md_dpath
from muleTrajectory import mt_dpath
from Markov1Step import m1s_dpath


mdt_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'muleDayTrajectory'])
if not opath.exists(mdt_dpath):
    os.mkdir(mdt_dpath)


def arrange_trajByDay(numEpoch=4):
    ep_dpath = opath.join(mdt_dpath, 'epoch%d' % numEpoch)
    if not opath.exists(ep_dpath):
        os.mkdir(ep_dpath)
    #
    month = 2
    muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % month, '_muleID-M%d.pkl' % month])
    with open(muleID_fpath, 'rb') as fp:
        madd_mid2, mid_madd2 = pickle.load(fp)
    lv_dh_madd = {lv: {} for lv in TARGET_LVS}
    for lv in TARGET_LVS:
        ofpath = reduce(opath.join, [m1s_dpath, 'epoch%d' % numEpoch, lv,
                                    '_M1SE%d-%s-muleDH.csv' % (numEpoch, lv)])
        with open(ofpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                dow, hour = [int(row[cn]) for cn in ['dow', 'hour']]
                lv_dh_madd[lv][dow, hour] = set([mid_madd2[int(_mid)] for _mid in eval(row['mules'])])
    month = 3
    muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % month, '_muleID-M%d.pkl' % month])
    with open(muleID_fpath, 'rb') as fp:
        madd_mid3, mid_madd3 = pickle.load(fp)
    aggMT_fpath = reduce(opath.join, [mt_dpath, 'epoch%d' % numEpoch, 'M%d' % month,
                                      'E%d-M%d-aggMuleTrajectory.csv' % (numEpoch, month)])
    lv_ddh_mules = {lv: {} for lv in TARGET_LVS}
    with open(aggMT_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv = row['lv']
            lv_dpath = opath.join(ep_dpath, lv)
            if not opath.exists(lv_dpath):
                os.mkdir(lv_dpath)
            month, day, dow, hour, epoch = [int(row[cn]) for cn in ['month', 'day', 'dow', 'hour', 'epoch']]
            mid = int(row['mid'])
            if mid_madd3[mid] not in lv_dh_madd[lv][dow, hour]:
                continue
            if (day, dow, hour) not in lv_ddh_mules[lv]:
                lv_ddh_mules[lv][day, dow, hour] = set()
            lv_ddh_mules[lv][day, dow, hour].add(mid)
            ofpath = opath.join(lv_dpath, 'mdt-%s-%02d%02d-H%02d-W%d.csv' % (lv, month, day, hour, dow))
            if not opath.exists(ofpath):
                with open(ofpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_header = ['month', 'day', 'dow', 'hour', 'epoch',
                                  'mid', 'absent', 'visitedLocs']
                    writer.writerow(new_header)
            new_row = [month, day, dow, hour, epoch,
                       mid, 1 if row['prevHourLoc'] == 'X' else 0, row['visitedLocs']]
            with open(ofpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)
    #
    for lv in TARGET_LVS:
        dh_mules_fpath = opath.join(ep_dpath, '_E%d-%s-muleDH.csv' % (numEpoch, lv))
        with open(dh_mules_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['day', 'dow', 'hour', 'numMules', 'mules']
            writer.writerow(new_header)
            for day, dow, hour in lv_ddh_mules[lv]:
                writer.writerow([day, dow, hour,
                                 len(lv_ddh_mules[lv][day, dow, hour]), list(lv_ddh_mules[lv][day, dow, hour])])


if __name__ == '__main__':
    # arrange_trajByDay(numEpoch=4)
    # arrange_trajByDay(numEpoch=2)
    arrange_trajByDay(numEpoch=1)