from xlrd import open_workbook

import os, fnmatch
import os.path as opath
import csv, gzip, time
from time import mktime
from datetime import datetime



floor = 'Lv4'


def get_zoneNlandmarkInfo():
    book = open_workbook('z_data/Landmarks.xlsx')
    sh = book.sheet_by_name('%s' % (floor))
    zones2landmarks, landmarks2zones = {}, {}
    for i in range(sh.nrows):
        for j in range(sh.ncols):
            if i < 1 or j < 1:
                continue
            zCoord = (i - 1, j - 1)
            if sh.cell(i, j).value:
                lid = '1010%s0%04d' % (floor[len('Lv'):], int(sh.cell(i, j).value))
                landmarks2zones[lid] = zCoord
                zones2landmarks[zCoord] = lid
            else:
                zones2landmarks[zCoord] = None
    #
    return zones2landmarks, landmarks2zones


def get_beaconInfo():
    book = open_workbook('z_data/BeaconLocation.xlsx')
    sh = book.sheet_by_name('BriefRepresentation')
    beacons2landmarks = {}
    floor_format = '0' + floor[len('Lv'):] + '0'
    numBeacons = 0
    for i in range(1, sh.nrows):
        locationID, landmarkID = map(str, map(int, [sh.cell(i, 0).value, sh.cell(i, 1).value]))
        lv = landmarkID[3:6]
        if floor_format == lv:
            numBeacons += 1
            beacons2landmarks[numBeacons] = landmarkID
    #
    return beacons2landmarks


def filter_muleTrajInfo():
    HOUR_9AM_6PM = [h for h in range(9, 18)]
    MON, TUE, WED, THR, FRI, SAT, SUN = range(7)
    floor_format = '0' + floor[len('Lv'):] + '0'
    with gzip.open('z_data/location_archival_2017_2_1.csv.gz', 'rt') as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
            if t.tm_wday is not TUE:
                continue
            if not t.tm_hour in HOUR_9AM_6PM:
                continue
            landmarkID = row['location']
            lv = landmarkID[3:6]
            if floor_format != lv:
                continue
            lv = 'Lv%s' % lv[1:-1]
            fpath = 'z_data/tra-%s-%d%02d%02d-H%02d.csv' % (lv, t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour)
            if not opath.exists(fpath):
                with open(fpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_headers = ['time', 'id', 'location']
                    writer.writerow(new_headers)
            with open(fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow([row['time'], row['id'], row['location']])


def get_muleStayingDuration():
    dpath = 'z_data/tra'
    indi_dpath = opath.join(dpath, 'individual')
    if not opath.exists(indi_dpath):
        os.mkdir(indi_dpath)
    hour, timeIntv = 10, 25
    mules = set()
    mules_fpath = {}
    for fn in os.listdir(dpath):
        if not fnmatch.fnmatch(fn, '*-H%02d.csv' % hour):
            continue
        mules_logs = {}
        with open(opath.join(dpath, fn)) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                curTime = datetime.fromtimestamp(mktime(t))
                mid = row['id']
                if mid not in mules_logs:
                    mules_logs[mid] = []
                mules_logs[mid].append((curTime, row['location']))
                mules.add(mid)
                if mid not in mules_fpath:
                    indi_tra_fpath = opath.join(indi_dpath, 'tra-%d.csv' % len(mules))
                    mules_fpath[mid] = indi_tra_fpath
                    with open(indi_tra_fpath, 'w') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        new_headers = ['id', 'location', 'timeSlot', 'duration', 'ft', 'tt']
                        writer.writerow(new_headers)
        for logs in mules_logs.values():
            logs.sort()
        for i, (mid, logs) in enumerate(mules_logs.items()):
            lastLoc, enterTime = None, None
            for curTime, loc in logs:
                if lastLoc is None:
                    lastLoc, enterTime = loc, curTime
                    continue
                if lastLoc != loc:
                    ts_ft = int(enterTime.minute/timeIntv)
                    ts_tt = int(curTime.minute / timeIntv)
                    if ts_ft == ts_tt:
                        duration = (curTime - enterTime).seconds
                        with open(mules_fpath[mid], 'a') as w_csvfile:
                            writer = csv.writer(w_csvfile, lineterminator='\n')
                            new_row = [mid, lastLoc, ts_ft, duration, enterTime, curTime]
                            writer.writerow(new_row)
                    else:
                        if ts_ft + 1 == ts_tt:
                            boundTime = datetime(enterTime.year, enterTime.month, enterTime.day,
                                              enterTime.hour, ts_tt * timeIntv)
                            duration1 = (boundTime - enterTime).seconds
                            duration2 = (curTime - boundTime).seconds
                            with open(mules_fpath[mid], 'a') as w_csvfile:
                                writer = csv.writer(w_csvfile, lineterminator='\n')
                                new_row = [mid, lastLoc, ts_ft, duration1, enterTime, boundTime]
                                writer.writerow(new_row)
                                new_row = [mid, lastLoc, ts_tt, duration2, boundTime, curTime]
                                writer.writerow(new_row)
                        else:
                            assert ts_ft + 2 == ts_tt, (ts_ft, ts_tt)

                            boundTime1 = datetime(enterTime.year, enterTime.month, enterTime.day,
                                                 enterTime.hour, (ts_ft + 1) * timeIntv)
                            boundTime2 = datetime(enterTime.year, enterTime.month, enterTime.day,
                                                 enterTime.hour, ts_tt * timeIntv)
                            duration1 = (boundTime1 - enterTime).seconds
                            duration2 = (boundTime2 - boundTime1).seconds
                            duration3 = (curTime - boundTime2).seconds
                            with open(mules_fpath[mid], 'a') as w_csvfile:
                                writer = csv.writer(w_csvfile, lineterminator='\n')
                                new_row = [mid, lastLoc, ts_ft, duration1, enterTime, boundTime1]
                                writer.writerow(new_row)
                                new_row = [mid, lastLoc, ts_ft + 1, duration2, boundTime2, boundTime1]
                                writer.writerow(new_row)
                                new_row = [mid, lastLoc, ts_tt, duration3, curTime, boundTime2]
                                writer.writerow(new_row)
                    lastLoc, enterTime = loc, curTime

def get_trajDist():
    import pandas as pd
    dpath = 'z_data/tra'
    indi_dpath = opath.join(dpath, 'individual')
    muleTraj2landmarks = []
    for fn in os.listdir(indi_dpath):
        if not fnmatch.fnmatch(fn, 'tra-*.csv'):
            continue
        df = pd.read_csv(opath.join(indi_dpath, fn))
        if len(df) <= 1:
            continue
        indi_muleTraj = [{}, {}, {}, {}]
        ts_dur = {}
        for timeSlot, durationSum in df.groupby(['timeSlot']).sum()['duration'].reset_index().values:
            ts_dur[timeSlot] = durationSum
        for loc, ts, dur in df.groupby(['location', 'timeSlot']).sum()['duration'].reset_index().values:
            indi_muleTraj[ts][loc] = dur / ts_dur[ts]
        muleTraj2landmarks.append(indi_muleTraj)
    return muleTraj2landmarks


if __name__ == '__main__':
    # get_beaconInfo()

    # filter_muleTrajInfo()
    # get_muleStayingDuration()
    # get_trajDist()
    pass