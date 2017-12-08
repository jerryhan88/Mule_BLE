import os.path as opath
import os, fnmatch
import csv, gzip
import datetime, time
import networkx as nx
import pickle
from xlrd import open_workbook

HOUR_9AM_6PM = [h for h in range(9, 18)]
MON, TUE, WED, THR, FRI, SAT, SUN = range(7)
N_TIMESLOT = 4
Intv = 60 / N_TIMESLOT


landmarks_fpath = opath.join('z_data', 'Landmarks.xlsx')
beacons_fpath = opath.join('z_data', 'BeaconLocation.xlsx')
rawTraj_fpath = opath.join('z_data', 'location_archival_2017_2_1.csv.gz')


def get_beaconInfo(floor):
    book = open_workbook(beacons_fpath)
    sh = book.sheet_by_name('BriefRepresentation')
    beacons2landmarks, landmarks2beacons = {}, {}
    floor_format = '0' + floor[len('Lv'):] + '0'
    for i in range(1, sh.nrows):
        beaconID, locationID = map(str, map(int, [sh.cell(i, 0).value, sh.cell(i, 1).value]))
        lv = locationID[3:6]
        landmarkId = str(int(locationID[-4:]))
        if floor_format == lv:
            beacons2landmarks[beaconID] = locationID
            if landmarkId not in landmarks2beacons:
                landmarks2beacons[landmarkId] = []
            landmarks2beacons[landmarkId].append(beaconID)
    #
    return beacons2landmarks, landmarks2beacons


def get_landmarkG(floor):
    landmarkG_fpath = opath.join('z_data', 'landmarkG-%s.pkl' % floor)
    if not opath.exists(landmarkG_fpath):
        book = open_workbook(landmarks_fpath)
        sh = book.sheet_by_name('%s' % (floor))
        #
        elist = []
        def handle_rb_edges(n0, i0, j0, sh, elist):
            for i1, j1 in [(i0 + 1, j0), (i0, j0 + 1)]:
                if sh.nrows <= i1 or sh.ncols <= j1:
                    continue
                cv1 = sh.cell(i1, j1).value
                if cv1 == '':
                    continue
                if type(cv1) == float:
                    n1 = str(int(cv1))
                    elist.append((n0, n1))
                elif ',' in cv1:
                    n1, n2 = cv1.split(',')
                    elist.append((n0, n1))
                    elist.append((n0, n2))
                else:
                    if ';' in cv1:
                        continue
                    elif 'd' in cv1:
                        n1 = cv1
                        elist.append((n0, n1))
                    else:
                        assert False

        for i0 in range(sh.nrows):
            for j0 in range(sh.ncols):
                if i0 < 1 or j0 < 1:
                    continue
                cv0 = sh.cell(i0, j0).value
                if cv0 == '':
                    continue
                if type(cv0) == float:
                    n0 = str(int(cv0))
                    handle_rb_edges(n0, i0, j0, sh, elist)
                elif ',' in cv0:
                    n00, n01 = cv0.split(',')
                    for n0 in [n00, n01]:
                        handle_rb_edges(n0, i0, j0, sh, elist)
                else:
                    if ';' in cv0:
                        n0, others = cv0.split(';')
                        n1, n2 = others.split('-')
                        elist.append((n0, n1))
                        elist.append((n0, n2))
                    elif 'd' in cv0:
                        n0 = cv0
                        handle_rb_edges(n0, i0, j0, sh, elist)
                    else:
                        assert False, (cv0, i0, j0)
        #
        G = nx.Graph()
        G.add_edges_from(elist)
        nx.write_gpickle(G, landmarkG_fpath)
    else:
        G = nx.read_gpickle(landmarkG_fpath)
    return G


def preprocess_rawTraj(floor, dow=TUE):
    floor_format = '0' + floor[len('Lv'):] + '0'
    dpath = opath.join('z_data', 'traj-%s-W%d' % (floor, dow))
    if not opath.exists(dpath):
        os.mkdir(dpath)
    with gzip.open(rawTraj_fpath, 'rt') as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
            if t.tm_wday is not dow:
                continue
            if not t.tm_hour in HOUR_9AM_6PM:
                continue
            locationID = row['location']
            lv = locationID[3:6]
            if floor_format != lv:
                continue
            lv = 'Lv%s' % lv[1:-1]
            fpath = opath.join(dpath,
                               'traj-%s-W%d-H%02d-%d%02d%02d.csv' % (lv, dow, t.tm_hour, t.tm_year, t.tm_mon, t.tm_mday))
            if not opath.exists(fpath):
                with open(fpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_headers = ['time', 'id', 'location']
                    writer.writerow(new_headers)
            with open(fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow([row['time'], row['id'], row['location']])


def gen_indiTrajectory(floor, dow=WED):
    lw_dpath = opath.join('z_data', 'traj-%s-W%d' % (floor, dow))
    mules_index = {}
    for hour in HOUR_9AM_6PM:
        indi_dpath = opath.join(lw_dpath, 'indiTraj-%s-W%d-H%02d' % (floor, dow, hour))
        if not opath.exists(indi_dpath):
            os.mkdir(indi_dpath)
        for fn in os.listdir(lw_dpath):
            if not fnmatch.fnmatch(fn, '*-H%02d-*.csv' % hour):
                continue
            prefix = fn[len('traj-'):-len('-20170201.csv')]
            suffix = fn[-len('20170201.csv'):]
            mules_ts_logs = {}
            with open(opath.join(lw_dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    curTime = datetime.datetime.fromtimestamp(time.mktime(t))
                    mid = row['id']
                    if mid not in mules_ts_logs:
                        mules_ts_logs[mid] = [[] for _ in range(N_TIMESLOT)]
                    if mid not in mules_index:
                        mules_index[mid] = len(mules_index)
                    k = int(curTime.minute / Intv)
                    mules_ts_logs[mid][k].append((curTime, row['location']))
            for mid, ts_logs in mules_ts_logs.items():
                for k, traj in enumerate(ts_logs):
                    if len(traj) < 2:
                        continue
                    traj.sort()
                    indi_tra_fpath = opath.join(indi_dpath, 'indiTraj-%s-K%d-m%d-%s' % (prefix, k, mules_index[mid], suffix))
                    with open(indi_tra_fpath, 'w') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        new_headers = ['fTime', 'tTime', 'duration', 'location']
                        writer.writerow(new_headers)
                        t0, l0 = None, ''
                        for t1, l1 in traj:
                            if t0 is None:
                                t0, l0 = t1, l1
                            if l1 != l0:
                                new_row = [t0, t1, (t1 - t0).seconds, l0]
                                writer.writerow(new_row)
                                t0, l0 = t1, l1
                        if l1 == l0:
                            new_row = [t0, t1, (t1 - t0).seconds, l0]
                            writer.writerow(new_row)


def aggregate_indiTrajectory(floor, dow=WED):
    G = get_landmarkG(floor)
    lw_dpath = opath.join('z_data', 'traj-%s-W%d' % (floor, dow))
    mids = set()
    for hour in HOUR_9AM_6PM:
        indi_dpath = opath.join(lw_dpath, 'indiTraj-%s-W%d-H%02d' % (floor, dow, hour))
        if not opath.exists(indi_dpath):
            continue
        for fn in os.listdir(indi_dpath):
            if not fnmatch.fnmatch(fn, '*.csv'):
                continue
            _, _, _, _, _, mid, _ = fn[:-len('.csv')].split('-')
            mids.add(mid)

    mids = sorted(list(mids))
    for hour in HOUR_9AM_6PM:
        fdh = '%s-W%d-H%02d' % (floor, dow, hour)
        indiTraj_prefix = 'indiTraj-%s' % fdh
        indi_dpath = opath.join(lw_dpath, indiTraj_prefix)
        fns = os.listdir(indi_dpath)
        #
        indiS_dpath = opath.join(lw_dpath, 'indiTrajS-%s' % fdh)
        if not opath.exists(indiS_dpath):
            os.mkdir(indiS_dpath)
        for mid in mids:
            indiTrajS_fpath = opath.join(indiS_dpath, 'indiTrajS-%s-%s.csv' % (fdh, mid))
            with open(indiTrajS_fpath, 'w') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                new_headers = ['date', 'timeslot', 'trajectories']
                writer.writerow(new_headers)
            for k in range(N_TIMESLOT):
                fnsF = [fn for fn in fns if fnmatch.fnmatch(fn, '%s-K%d-%s-*.csv' % (indiTraj_prefix, k, mid))]
                if not fnsF:
                    continue
                for fn in fnsF:
                    _, _, _, _, _, _, yyyymmdd = fn[:-len('.csv')].split('-')
                    trajectories = set()
                    with open(opath.join(indi_dpath, fn), 'rt') as r_csvfile:
                        reader = csv.DictReader(r_csvfile)
                        prevLM = None
                        for row in reader:
                            locationID = row['location']
                            curLM = str(int(locationID[-4:]))
                            if prevLM is not None:
                                trajectories.add(tuple(nx.shortest_path(G, prevLM, curLM)))
                            prevLM = curLM
                        if not trajectories:
                            trajectories.add(prevLM)
                    with open(indiTrajS_fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        new_row = [yyyymmdd, k, list(trajectories)]
                        writer.writerow(new_row)


if __name__ == '__main__':
    floor = 'Lv4'
    # gen_indiTrajectory(floor)
    aggregate_indiTrajectory(floor, dow=0)
    #
    # for dow in [
    #             # MON,
    #             # TUE,
    #             WED,
    #             # THR, FRI
    #             ]:
    #     preprocess_rawTraj(floor, dow)

    # get_muleTrajectory(10)
