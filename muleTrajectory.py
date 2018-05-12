import os.path as opath
import os
import csv, pickle
from functools import reduce
#
from beaconLayout import get_lmPairSP
from muleDuration import get_dt, md_dpath


MIN60 = 60
#
# Output directory path
#
mt_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'muleTrajectory'])
if not opath.exists(mt_dpath):
    os.mkdir(mt_dpath)


def gen_muleTrajectory(month, lv, numEpoch=4):
    def get_M2_muleInfo():
        m2 = 2
        am_fpath = reduce(opath.join, [md_dpath, 'M%d' % m2, '_activeMules-M%d.pkl' % m2])
        with open(am_fpath, 'rb') as fp:
            m2_active_mids = pickle.load(fp)
        muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % m2, '_muleID-M%d.pkl' % m2])
        with open(muleID_fpath, 'rb') as fp:
            m2_madd_mid, _ = pickle.load(fp)
        return m2_active_mids, m2_madd_mid
    #
    ep_dpath = opath.join(mt_dpath, 'epoch%d' % numEpoch)
    month_dpath = opath.join(ep_dpath, 'M%d' % month)
    lv_dpath = opath.join(month_dpath, lv)
    for dpath in [ep_dpath, month_dpath, lv_dpath]:
        if not opath.exists(dpath):
            os.mkdir(dpath)
    Intv = MIN60 / numEpoch
    #
    m2_active_mids, m2_madd_mid = get_M2_muleInfo()
    lmPairSP = get_lmPairSP(lv)
    muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % month, '_muleID-M%d.pkl' % month])
    with open(muleID_fpath, 'rb') as fp:
        madd_mid, mid_madd = pickle.load(fp)
    indiDur_dpath = reduce(opath.join, [md_dpath, 'M%d' % month, lv, 'individual'])
    for fn in sorted([fn for fn in os.listdir(indiDur_dpath) if fn.endswith('.csv')]):
        _, _, _, _mid = fn[:-len('.csv')].split('-')
        mid = int(_mid[1:])
        if month == 2:
            if mid not in m2_active_mids:
                continue
        else:
            assert month == 3
            if mid_madd[mid] not in m2_madd_mid:
                continue
            if m2_madd_mid[mid_madd[mid]] not in m2_active_mids:
                continue
        ifpath = opath.join(indiDur_dpath, fn)
        ofpath = opath.join(lv_dpath, 'MTE%d-M%d-%s-%s.csv' % (numEpoch, month, lv, _mid))
        with open(ofpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['month', 'day', 'hour', 'epoch', 'fLoc', 'tLoc', 'trajectory', 'dow', 'bTime', 'eTime']
            writer.writerow(new_header)
            #
            handling_day = - 1
            prevTime, fLoc = None, None
            with open(ifpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    cTime_dt = get_dt(row['fTime'])
                    tLoc = str(int(row['location'][-4:]))
                    if handling_day != cTime_dt.day:
                        pTime_dt, fLoc = cTime_dt, str(int(row['location'][-4:]))
                        handling_day = cTime_dt.day
                        continue
                    new_row = [pTime_dt.month, pTime_dt.day, pTime_dt.hour, int(pTime_dt.minute / Intv),
                               fLoc, tLoc, tuple(lmPairSP[fLoc, tLoc]),
                               pTime_dt.weekday(), pTime_dt, cTime_dt]
                    writer.writerow(new_row)
                    #
                    pTime_dt, fLoc = cTime_dt, tLoc


def aggregate_muleTrajectory(month, numEpoch=4):
    def append_row(fpath, row):
        with open(fpath, 'a') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            writer.writerow(row)
    #
    month_dpath = reduce(opath.join, [mt_dpath, 'epoch%d' % numEpoch, 'M%d' % month])
    aggMT_fpath = opath.join(month_dpath, 'E%d-M%d-aggMuleTrajectory.csv' % (numEpoch, month))
    with open(aggMT_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['lv', 'month', 'day', 'dow',
                      'mid', 'hour', 'prevHourLoc', 'epoch', 'visitedLocs', 'bTime', 'eTime']
        writer.writerow(new_header)
    #
    for lv in os.listdir(month_dpath):
        if not opath.isdir(opath.join(month_dpath, lv)):
            continue
        lv_dpath = opath.join(month_dpath, lv)
        for fn in sorted([fn for fn in os.listdir(lv_dpath) if fn.endswith('.csv')]):
            _, _, _, _mid = fn[:-len('.csv')].split('-')
            mid = int(_mid[1:])
            ifpath = opath.join(lv_dpath, fn)
            day0, dow0, hour0, hourPrevLoc0 = -1, -1, -1, 'X'
            epoch0, visitedLocs = -1, set()
            bTime0, eTime0 = None, None
            lastLoc = None
            with open(ifpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    day, dow, hour, epoch, fLoc, tLoc = [row[cn] for cn in ['day', 'dow', 'hour', 'epoch', 'fLoc', 'tLoc']]
                    trajectory = eval(row['trajectory'])
                    bTime, eTime = [get_dt(row[cn])for cn in ['bTime', 'eTime']]
                    if day0 != day:
                        if day0 != -1:
                            new_row = [lv, month, day0, dow0,
                                       mid, hour0, hourPrevLoc0, epoch0, sorted(list(visitedLocs)), bTime0, eTime0]
                            append_row(aggMT_fpath, new_row)
                        day0, dow0, hour0, hourPrevLoc0 = day, dow, hour, 'X'
                        epoch0 = epoch
                        visitedLocs = set()
                        for loc in trajectory:
                            visitedLocs.add(loc)
                        bTime0, eTime0 = bTime, eTime
                    else:
                        if hour0 == hour and epoch0 == epoch:
                            for loc in trajectory:
                                visitedLocs.add(loc)
                            eTime0 = eTime
                        elif hour0 == hour and epoch0 != epoch:
                            new_row = [lv, month, day0, dow0,
                                       mid, hour0, hourPrevLoc0, epoch0, sorted(list(visitedLocs)), bTime0, eTime0]
                            append_row(aggMT_fpath, new_row)
                            #
                            epoch0 = epoch
                            bTime0, eTime0 = bTime, eTime
                            visitedLocs = set()
                            for loc in trajectory:
                                visitedLocs.add(loc)
                        else:
                            assert hour0 != hour
                            if eval(hour0) + 1 != eval(hour):
                                hourPrevLoc0 = 'X'
                            new_row = [lv, month, day0, dow0,
                                       mid, hour0, hourPrevLoc0, epoch0, sorted(list(visitedLocs)), bTime0, eTime0]
                            append_row(aggMT_fpath, new_row)
                            #
                            hour0, hourPrevLoc0 = hour, lastLoc
                            epoch0 = epoch
                            bTime0, eTime0 = bTime, eTime
                            visitedLocs = set()
                            for loc in trajectory:
                                visitedLocs.add(loc)
                    lastLoc = tLoc


if __name__ == '__main__':
    # gen_muleTrajectory(3, 'Lv2', numEpoch=1)
    # gen_muleTrajectory(3, 'Lv4', numEpoch=1)
    # aggregate_muleTrajectory(2, numEpoch=2)
    # aggregate_muleTrajectory(2, numEpoch=1)
    # aggregate_muleTrajectory(3, numEpoch=1)
    aggregate_muleTrajectory(3, numEpoch=2)
