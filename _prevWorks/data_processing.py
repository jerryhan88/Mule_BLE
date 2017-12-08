from xlrd import open_workbook

import os, fnmatch
import os.path as opath
import pickle
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


def get_muleTrajectory():
    dpath = 'z_data/tra'
    indi_dpath = opath.join(dpath, 'individual')
    if not opath.exists(indi_dpath):
        os.mkdir(indi_dpath)
    hour, numTimeSlot, timeIntv = 10, 4, 25
    mules_index = {}
    for fn in os.listdir(dpath):
        if not fnmatch.fnmatch(fn, '*-H%02d.csv' % hour):
            continue
        prefix = fn[:-len('.csv')]
        mules_ts_logs = {}
        with open(opath.join(dpath, fn)) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                curTime = datetime.fromtimestamp(mktime(t))
                mid = row['id']
                if mid not in mules_ts_logs:
                    mules_ts_logs[mid] = [[] for _ in range(numTimeSlot)]
                if mid not in mules_index:
                    mules_index[mid] = len(mules_index)
                ts = int(curTime.minute/timeIntv)
                mules_ts_logs[mid][ts].append((curTime, row['location']))
        #
        for mid, ts_logs in mules_ts_logs.items():
            for ts, traj in enumerate(ts_logs):
                if len(traj) < 2:
                    continue
                traj.sort()
                indi_tra_fpath = opath.join(indi_dpath, '%s-%d-%d.pkl' % (prefix, mules_index[mid], ts))
                with open(indi_tra_fpath, 'wb') as fp:
                    pickle.dump(traj, fp)


def get_trajWinterM():
    dpath = 'z_data/tra'
    indi_dpath = opath.join(dpath, 'individual')
    fpath = opath.join(indi_dpath, 'tra-Lv4-20170207-H10-2-1.pkl')
    traj = None
    with open(fpath, 'rb') as fp:
        traj = pickle.load(fp)

    print(traj)


#
# def get_trajDist():
#     import pandas as pd
#     dpath = 'z_data/tra'
#     indi_dpath = opath.join(dpath, 'individual')
#     muleTraj2landmarks = []
#     for fn in os.listdir(indi_dpath):
#         if not fnmatch.fnmatch(fn, 'tra-*.csv'):
#             continue
#         df = pd.read_csv(opath.join(indi_dpath, fn))
#         if len(df) <= 1:
#             continue
#         indi_muleTraj = [{}, {}, {}, {}]
#         ts_dur = {}
#         for timeSlot, durationSum in df.groupby(['timeSlot']).sum()['duration'].reset_index().values:
#             ts_dur[timeSlot] = durationSum
#         for loc, ts, dur in df.groupby(['location', 'timeSlot']).sum()['duration'].reset_index().values:
#             indi_muleTraj[ts][loc] = dur / ts_dur[ts]
#         muleTraj2landmarks.append(indi_muleTraj)
#     return muleTraj2landmarks


if __name__ == '__main__':
    # get_beaconInfo()

    # filter_muleTrajInfo()
    # get_muleStayingDuration()
    # get_trajDist()
    # get_muleTrajectory()
    get_trajWinterM()