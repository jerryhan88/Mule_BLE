import os.path as opath
import os, fnmatch, shutil
import multiprocessing
import datetime, time
import networkx as nx
import pandas as pd
from math import sqrt
from xlrd import open_workbook
import csv, gzip
import pickle
from functools import reduce


HOUR_9AM_6PM = [h for h in range(9, 18)]
MON, TUE, WED, THR, FRI, SAT, SUN = range(7)
WEEK_DAYS = [MON, TUE, WED, THR, FRI]
N_TIMESLOT = 4
Intv = 60 / N_TIMESLOT
PL_RANGE = [3, 7, 10]
PL_CUNSUME = [1, 6.3095734447, 15.8489319246]
MIN_BATTERY_POWER, MAX_BATTERY_POWER = 980, 1000
LEAST_DAYS = 4
TARGET_LVS = {'Lv2', 'Lv4'}
EPOCH_LEAST_RECORDS = 3

landmarks_fpath = opath.join('z_data', 'Landmarks.xlsx')
beacons_fpath = opath.join('z_data', 'BeaconLocation.xlsx')
rawTraj2_fpath = opath.join('z_data', 'location_archival_2017_2_1.csv.gz')
rawTraj3_fpath = opath.join('z_data', 'location_archival_2017_3_1.csv.gz')


get_dt = lambda tf_str: datetime.datetime.fromtimestamp(time.mktime(time.strptime(tf_str, "%Y-%m-%d %H:%M:%S")))


def get_base_dpath(month):
    if month == 2:
        base_dpath = opath.join('z_data', 'M2')
    else:
        assert month == 3
        base_dpath = opath.join('z_data', 'M3')
    if not opath.exists(base_dpath):
        os.mkdir(base_dpath)
    return base_dpath


def get_beacon2landmark(floor):
    beaconInfo_fpath = opath.join('z_data', 'beaconInfo-%s.pkl' % floor)
    if not opath.exists(beaconInfo_fpath):
        book = open_workbook(beacons_fpath)
        sh = book.sheet_by_name('BriefRepresentation')
        beacon2landmark = {}
        floor_format = '0' + floor[len('Lv'):] + '0'
        markedLandmarkID = set()
        for i in range(1, sh.nrows):
            beaconID, locationID = map(str, map(int, [sh.cell(i, 0).value, sh.cell(i, 1).value]))
            lv = locationID[3:6]
            landmarkID = str(int(locationID[-4:]))
            if landmarkID in markedLandmarkID:
                continue
            if floor_format == lv:
                beacon2landmark[beaconID] = landmarkID
                markedLandmarkID.add(landmarkID)
        with open(beaconInfo_fpath, 'wb') as fp:
            pickle.dump(beacon2landmark, fp)
    else:
        with open(beaconInfo_fpath, 'rb') as fp:
            beacon2landmark = pickle.load(fp)
    #
    return beacon2landmark


def get_gridLayout(floor):
    gridLayout_fpath = opath.join('z_data', 'gridLayout-%s.pkl' % floor)
    if not opath.exists(gridLayout_fpath):
        book = open_workbook(landmarks_fpath)
        sh = book.sheet_by_name('%s' % (floor))
        grid_lmID = {}
        for i0 in range(sh.ncols):
            for j0 in range(sh.nrows):
                if j0 < 1 or i0 < 1:
                    continue
                cv0 = sh.cell(j0, i0).value
                if cv0 == '':
                    continue
                if type(cv0) == float:
                    n0 = str(int(cv0))
                    grid_lmID[i0, j0] = n0
                elif ',' in cv0:
                    n00, n01 = cv0.split(',')
                    grid_lmID[i0, j0] = [n00, n01]
                else:
                    if ';' in cv0:
                        n0, others = cv0.split(';')
                        grid_lmID[i0, j0] = n0
                    elif 'd' in cv0:
                        n0 = cv0
                        grid_lmID[i0, j0] = n0
                    else:
                        assert False, (cv0, i0, j0)
        #
        numCols, numRows = sh.ncols, sh.nrows
        with open(gridLayout_fpath, 'wb') as fp:
            pickle.dump([sh.ncols, sh.nrows, grid_lmID], fp)
    else:
        with open(gridLayout_fpath, 'rb') as fp:
            numCols, numRows, grid_lmID = pickle.load(fp)
    #
    return numCols, numRows, grid_lmID


def get_bzDist(floor):
    #
    # Euclidean distance
    #
    bzDist_fpath = opath.join('z_data', 'bzDist-%s.pkl' % floor)
    if not opath.exists(bzDist_fpath):
        numCols, numRows, grid_lmID = get_gridLayout(floor)
        zones, lmID2zone = {}, {}
        for zi in range(numCols):
            for zj in range(numRows):
                if (zi, zj) not in grid_lmID:
                    continue
                _lmID = grid_lmID[zi, zj]
                if type(_lmID) == list:
                    for lmID in _lmID:
                        lmID2zone[lmID] = (zi, zj)
                else:
                    lmID2zone[_lmID] = (zi, zj)
        #
        bzDist = {}
        beacon2landmark = get_beacon2landmark(floor)
        for beaconID in beacon2landmark:
            b_zi, b_zj = lmID2zone[beacon2landmark[beaconID]]
            bzDist[beaconID] = {}
            for zi in range(numCols):
                for zj in range(numRows):
                    bzDist[beaconID][zi, zj] = sqrt((b_zi - zi) ** 2 + (b_zj - zj) ** 2)
        with open(bzDist_fpath, 'wb') as fp:
            pickle.dump(bzDist, fp)
    else:
        with open(bzDist_fpath, 'rb') as fp:
            bzDist = pickle.load(fp)
    #
    return bzDist


def get_plCovLD(floor):
    plCovLD_fpath = opath.join('z_data', 'plCovLD-%s.pkl' % floor)
    if not opath.exists(plCovLD_fpath):
        plCovLD = {}
        _, _, grid_lmID = get_gridLayout(floor)
        bzDist = get_bzDist(floor)
        for bid in bzDist:
            for l, rd in enumerate(PL_RANGE):
                plCovLD[bid, l] = []
                for zi, zj in bzDist[bid]:
                    if (zi, zj) not in grid_lmID:
                        continue
                    if bzDist[bid][zi, zj] > rd:
                        continue
                    _lmID = grid_lmID[zi, zj]
                    if type(_lmID) == list:
                        for lmID in _lmID:
                            plCovLD[bid, l].append(lmID)
                    else:
                        plCovLD[bid, l].append(_lmID)
        with open(plCovLD_fpath, 'wb') as fp:
            pickle.dump(plCovLD, fp)
    else:
        with open(plCovLD_fpath, 'rb') as fp:
            plCovLD = pickle.load(fp)
    #
    return plCovLD


def get_lmPairSP(floor):
    #
    # Get all landmark pairs' shortest path
    #
    lmPairSP_fpath = opath.join('z_data', 'lmPairSP-%s.pkl' % floor)
    if not opath.exists(lmPairSP_fpath):
        book = open_workbook(landmarks_fpath)
        sh = book.sheet_by_name('%s' % (floor))
        #
        elist = []
        def handle_rb_edges(n0, i0, j0, sh, elist):
            for i1, j1 in [(i0 + 1, j0), (i0, j0 + 1)]:
                if sh.ncols <= i1 or sh.nrows <= j1:
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
        #
        for i0 in range(sh.ncols):
            for j0 in range(sh.nrows):
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
                        if '-' not in cv0:
                            continue
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
        N = G.nodes()
        lmPairSP = {}
        for lm1 in N:
            for lm2 in N:
                if lm1 == lm2:
                    continue
                lmPairSP[lm1, lm2] = tuple(nx.shortest_path(G, lm1, lm2))
        with open(lmPairSP_fpath, 'wb') as fp:
            pickle.dump(lmPairSP, fp)
    else:
        with open(lmPairSP_fpath, 'rb') as fp:
            lmPairSP = pickle.load(fp)
    return lmPairSP


def get_plCovTraj(floor):
    plCovTraj_fpath = opath.join('z_data', 'plCovTraj-%s.pkl' % floor)
    if not opath.exists(plCovTraj_fpath):
        plCovLD = get_plCovLD(floor)
        lmPairSP = get_lmPairSP(floor)
        plCovTraj = {}
        for (bid, l), lms in plCovLD.items():
            plCovTraj[bid, l] = []
            covLM = set(lms)
            for lmPair, pathSeq in lmPairSP.items():
                if covLM.intersection(set(pathSeq)):
                    plCovTraj[bid, l].append(lmPair)
        with open(plCovTraj_fpath, 'wb') as fp:
            pickle.dump(plCovTraj, fp)
    else:
        with open(plCovTraj_fpath, 'rb') as fp:
            plCovTraj = pickle.load(fp)
    return plCovTraj



def month2LvDay(month):
    month_dpath = get_base_dpath(month)
    if not opath.exists(month_dpath):
        os.mkdir(month_dpath)
    muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
    madd_mid, mid_madd = {}, {}
    #
    rawTraj_fpath = rawTraj2_fpath if month == 2 else rawTraj3_fpath
    with gzip.open(rawTraj_fpath, 'rt') as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            t = time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
            if not t.tm_wday in WEEK_DAYS:
                continue
            if not t.tm_hour in HOUR_9AM_6PM:
                continue
            locationID = row['location']
            lv = locationID[3:6]
            lv = 'Lv%s' % lv[1:-1]
            lv_dpath = opath.join(month_dpath, 'M%d-%s' % (month, lv))
            if not opath.exists(lv_dpath):
                os.mkdir(lv_dpath)
            fpath = opath.join(lv_dpath, 'M%d-%s-%d%02d%02d.csv' % (month, lv, t.tm_year, t.tm_mon, t.tm_mday))
            if not opath.exists(fpath):
                with open(fpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_headers = ['time', 'id', 'location']
                    writer.writerow(new_headers)
            madd = row['id']
            if madd not in madd_mid:
                mid = len(madd_mid)
                madd_mid[madd] = mid
                mid_madd[mid] = madd

            with open(fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow([row['time'], row['id'], row['location']])
    with open(muleID_fpath, 'wb') as fp:
        pickle.dump([madd_mid, mid_madd], fp)


def individual_duration(month):
    month_dpath = get_base_dpath(month)
    muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
    with open(muleID_fpath, 'rb') as fp:
        madd_mid, mid_madd = pickle.load(fp)

    def handle_lv_individual_duration(dpath):
        indi_dpath = opath.join(dpath, 'indiDur')
        if opath.exists(indi_dpath):
            shutil.rmtree(indi_dpath)
        os.mkdir(indi_dpath)
        for fn in sorted([fn for fn in os.listdir(dpath) if fn.endswith('.csv')]):
            if not fn.endswith('.csv'):
                continue
            print(fn)
            lv = fn.split('-')[1]
            mule_traj = {}
            with open(opath.join(dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    t1 = get_dt(row['time'])
                    madd, loc1 = [row[cn] for cn in ['id', 'location']]
                    if madd not in mule_traj:
                        mule_traj[madd] = []
                    mule_traj[madd].append((t1, loc1))
            print('read all records', fn)
            for madd, traj in mule_traj.items():
                fpath = opath.join(indi_dpath, 'M%d-%s-m%d.csv' % (month, lv, madd_mid[madd]))
                if not opath.exists(fpath):
                    with open(fpath, 'w') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        new_header = ['mid', 'fTime', 'tTime', 'duration', 'location']
                        writer.writerow(new_header)
                with open(fpath, 'a') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    t0, loc0 = None, None
                    for t1, loc1 in sorted(traj):
                        if t0 is None:
                            t0, loc0 = t1, loc1
                            continue
                        if loc1 == loc0:
                            continue
                        else:
                            writer.writerow([madd_mid[madd], t0, t1, (t1 - t0).seconds, loc0])
                            t0, loc0 = t1, loc1
    #
    lvs_dpath = sorted([opath.join(month_dpath, dname) for dname in os.listdir(month_dpath) if opath.isdir(opath.join(month_dpath, dname))])
    ps = []
    for dpath in lvs_dpath:
        p = multiprocessing.Process(target=handle_lv_individual_duration, args=(dpath, ))
        ps.append(p)
        p.start()
    for p in ps:
        p.join()


def aggregate_indiDur(month):
    month_dpath = get_base_dpath(month)
    indiDur_fpath = opath.join(month_dpath, 'M%d-aggIndiDur.csv' % month)
    #
    muleDayLv_duration = {}
    lvs_dpath = [opath.join(month_dpath, dname) for dname in os.listdir(month_dpath) if
                 opath.isdir(opath.join(month_dpath, dname))]
    mids, days, lvs = set(), set(), set()
    for lv_dpath in lvs_dpath:
        indi_dpath = opath.join(lv_dpath, 'indiDur')
        for fn in os.listdir(indi_dpath):
            if not fn.endswith('.csv'):
                continue
            lv = fn.split('-')[1]
            with open(opath.join(indi_dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    t = time.strptime(row['fTime'], "%Y-%m-%d %H:%M:%S")
                    mid = row['mid']
                    k = (mid, t.tm_mday, lv)
                    if k not in muleDayLv_duration:
                        muleDayLv_duration[k] = 0
                        mids.add(mid)
                        days.add(t.tm_mday)
                        lvs.add(lv)
                    muleDayLv_duration[k] += eval(row['duration'])
    with open(indiDur_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['month', 'day', 'lv', 'mid', 'duration']
        writer.writerow(new_header)
        for day in days:
            for lv in lvs:
                for mid in mids:
                    k = (mid, day, lv)
                    if k in muleDayLv_duration:
                        writer.writerow([month, day, lv, mid, muleDayLv_duration[k]])


def filter_mules(month):
    am_fpath = opath.join(get_base_dpath(month), '_activeMules-M%d.pkl' % month)
    #
    df = pd.read_csv(opath.join(get_base_dpath(month), 'M2-aggIndiDur.csv'))
    df = df.groupby(['mid', 'day']).sum()['duration'].reset_index()
    df = df.groupby(['mid']).count()['day'].to_frame('days').reset_index()
    df = df[(df['days'] > LEAST_DAYS)]
    active_mids = set(df['mid'])
    print("# active mules in Feb.: %d" % len(active_mids))
    with open(am_fpath, 'wb') as fp:
        pickle.dump(active_mids, fp)


def gen_indiTrajectory(month):
    m2 = 2
    with open(opath.join(get_base_dpath(m2), '_activeMules-M%d.pkl' % m2), 'rb') as fp:
        active_mids = pickle.load(fp)
    with open(opath.join(get_base_dpath(m2), '_muleID-M%d.pkl' % m2), 'rb') as fp:
        m2_madd_mid, _ = pickle.load(fp)
    #
    month_dpath = get_base_dpath(month)
    muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
    with open(muleID_fpath, 'rb') as fp:
        madd_mid, mid_madd = pickle.load(fp)
    for dname in os.listdir(month_dpath):
        if not opath.isdir(opath.join(month_dpath, dname)):
            continue
        _, lv = dname.split('-')
        if lv not in TARGET_LVS:
            continue
        lmPairSP = get_lmPairSP(lv)
        #
        lv_dpath = opath.join(month_dpath, dname)
        indiDur_dpath = opath.join(lv_dpath, 'indiDur')
        indiTraj_dpath = opath.join(lv_dpath, 'indiTraj')
        if opath.exists(indiTraj_dpath):
            shutil.rmtree(indiTraj_dpath)
        os.mkdir(indiTraj_dpath)
        for fn in sorted([fn for fn in os.listdir(indiDur_dpath) if fn.endswith('.csv')]):
            _, _, _mid = fn[:-len('.csv')].split('-')
            mid = int(_mid[1:])
            if month == 2:
                if mid not in active_mids:
                    continue
            else:
                assert month == 3
                if mid_madd[mid] not in m2_madd_mid:
                    continue
                if m2_madd_mid[mid_madd[mid]] not in active_mids:
                    continue
            ifpath = opath.join(indiDur_dpath, fn)
            ofpath = opath.join(indiTraj_dpath, fn)
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



def aggregate_indiTraj(month):
    def append_row(fpath, row):
        with open(fpath, 'a') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            writer.writerow(row)
    #
    month_dpath = get_base_dpath(month)
    indiTraj_fpath = opath.join(month_dpath, 'M%d-aggIndiTraj.csv' % month)
    with open(indiTraj_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['lv', 'month', 'day', 'dow',
                      'mid', 'hour', 'prevHourLoc', 'epoch', 'visitedLocs', 'bTime', 'eTime']
        writer.writerow(new_header)
    #
    for dname in os.listdir(month_dpath):
        if not opath.isdir(opath.join(month_dpath, dname)):
            continue
        _, lv = dname.split('-')
        if lv not in TARGET_LVS:
            continue
        lv_dpath = opath.join(month_dpath, dname)
        indiTraj_dpath = opath.join(lv_dpath, 'indiTraj')
        for fn in sorted([fn for fn in os.listdir(indiTraj_dpath) if fn.endswith('.csv')]):
            _, _, _mid = fn[:-len('.csv')].split('-')
            mid = int(_mid[1:])
            ifpath = opath.join(indiTraj_dpath, fn)
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
                            append_row(indiTraj_fpath, new_row)
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
                            append_row(indiTraj_fpath, new_row)
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
                            append_row(indiTraj_fpath, new_row)
                            #
                            hour0, hourPrevLoc0 = hour, lastLoc
                            epoch0 = epoch
                            bTime0, eTime0 = bTime, eTime
                            visitedLocs = set()
                            for loc in trajectory:
                                visitedLocs.add(loc)
                    lastLoc = tLoc


def gen_indiCouting(month):
    month_dpath = get_base_dpath(month)
    indiCouting_fpath = opath.join(month_dpath, 'M%d-aggIndiCouting.csv' % month)
    with open(indiCouting_fpath, 'w') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        new_header = ['lv', 'month', 'mid',
                      'dow', 'hour', 'epoch',
                      'absent', 'nReocrds', 'nVisitedLocs']
        writer.writerow(new_header)
    #
    indiTraj_fpath = opath.join(month_dpath, 'M%d-aggIndiTraj.csv' % month)
    ks = [set() for _ in range(5)]
    indiCouting = {}
    indiCoutingDetail = {}
    with open(indiTraj_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv, mid, dow, hour, epoch = [row[cn] for cn in ['lv', 'mid', 'dow', 'hour', 'epoch']]
            k0 = [lv, mid, dow, hour, epoch]
            for i, ele in enumerate(k0):
                ks[i].add(ele)
            absent = 1 if row['prevHourLoc'] == 'X' else 0
            k1 = tuple(k0 + [absent])
            if k1 not in indiCouting:
                indiCouting[k1] = 0
                indiCoutingDetail[k1] = {}
            indiCouting[k1] += 1
            for loc in eval(row['visitedLocs']):
                if loc not in indiCoutingDetail[k1]:
                    indiCoutingDetail[k1][loc] = 0
                indiCoutingDetail[k1][loc] += 1
    with open(indiCouting_fpath, 'a') as w_csvfile:
        writer = csv.writer(w_csvfile, lineterminator='\n')
        lvs, mids, dows, hours, epochs = ks
        for lv in lvs:
            for mid in sorted(list(mids)):
                for dow in sorted(list(dows)):
                    for hour in sorted(list(hours)):
                        for epoch in sorted(list(epochs)):
                            k0 = (lv, mid, dow, hour, epoch, 0)
                            k1 = (lv, mid, dow, hour, epoch, 1)
                            if k0 in indiCouting and k1 in indiCouting:
                                if indiCouting[k0] + indiCouting[k1] < EPOCH_LEAST_RECORDS:
                                    continue
                                writer.writerow([lv, month, mid,
                                                 dow, hour, epoch,
                                                 0, indiCouting[k0], indiCoutingDetail[k0]])
                                writer.writerow([lv, month, mid,
                                                 dow, hour, epoch,
                                                 1, indiCouting[k1], indiCoutingDetail[k1]])
                            else:
                                if k0 in indiCouting:
                                    assert k1 not in indiCouting
                                    if indiCouting[k0] < EPOCH_LEAST_RECORDS:
                                        continue
                                    writer.writerow([lv, month, mid,
                                                     dow, hour, epoch,
                                                     0, indiCouting[k0], indiCoutingDetail[k0]])
                                elif k1 in indiCouting:
                                    assert k0 not in indiCouting
                                    if indiCouting[k1] < EPOCH_LEAST_RECORDS:
                                        continue
                                    writer.writerow([lv, month, mid,
                                                     dow, hour, epoch,
                                                     1, indiCouting[k1], indiCoutingDetail[k1]])


def gen_p_kmbl():
    month = 2
    month_dpath = get_base_dpath(month)
    indiCouting_fpath = opath.join(month_dpath, 'M%d-aggIndiCouting.csv' % month)
    bids, plCovLD = {}, {}
    with open(indiCouting_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv = row['lv']
            lv_dpath = opath.join(month_dpath, 'M%d-%s' % (month, lv))
            p_dpath = opath.join(lv_dpath, 'p_kmbl')
            if not opath.exists(p_dpath):
                os.mkdir(p_dpath)
            mid = row['mid']
            _mid = 'm%s' % mid
            fpath = opath.join(p_dpath, 'M%d-%s-%s.csv' % (month, lv, _mid))
            if not opath.exists(fpath):
                with open(fpath, 'w') as w_csvfile:
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
                    with open(fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow(new_row)


def arrange_p_kmbl():
    month = 2
    month_dpath = get_base_dpath(month)

    for dname in os.listdir(month_dpath):
        if not opath.isdir(opath.join(month_dpath, dname)):
            continue
        _, lv = dname.split('-')
        if lv not in TARGET_LVS:
            continue
        lv_dpath = opath.join(month_dpath, dname)
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
                    fpath = opath.join(p1_dpath, 'W%d-H%02d.csv' % (dow, hour))
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
        dh_mules_fpath = opath.join(month_dpath, '__M%d-%s-muleDH.csv' % (month, lv))
        with open(dh_mules_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['dow', 'hour', 'numMules', 'mules']
            writer.writerow(new_header)
            for dow, hour in dh_mules:
                writer.writerow([dow, hour, len(dh_mules[dow, hour]), list(dh_mules[dow, hour])])
        p_kmbl_fpath = opath.join(month_dpath, '_M%d-%s-p_kmbl.pkl' % (month, lv))
        with open(p_kmbl_fpath, 'wb') as fp:
            pickle.dump(dh_p_kmbl, fp)


def arrange_trajByDay():
    month = 2
    month_dpath = get_base_dpath(month)
    muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
    with open(muleID_fpath, 'rb') as fp:
        madd_mid2, mid_madd2 = pickle.load(fp)
    lv_dh_madd = {lv: {} for lv in TARGET_LVS}
    for lv in TARGET_LVS:
        fpath = opath.join(month_dpath, '__M%d-%s-muleDH.csv' % (month, lv))
        with open(fpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                dow, hour = [int(row[cn]) for cn in ['dow', 'hour']]
                lv_dh_madd[lv][dow, hour] = set([mid_madd2[int(_mid)] for _mid in eval(row['mules'])])
    month = 3
    month_dpath = get_base_dpath(month)
    muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
    with open(muleID_fpath, 'rb') as fp:
        madd_mid3, mid_madd3 = pickle.load(fp)
    indiTraj_fpath = opath.join(month_dpath, 'M%d-aggIndiTraj.csv' % month)
    lv_ddh_mules = {lv: {} for lv in TARGET_LVS}
    with open(indiTraj_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv = row['lv']
            month, day, dow, hour, epoch = [int(row[cn]) for cn in ['month', 'day', 'dow', 'hour', 'epoch']]
            trajBD_dpath = reduce(opath.join, [month_dpath, 'M%d-%s' % (month, lv), 'trajByDay'])
            if not opath.exists(trajBD_dpath):
                os.mkdir(trajBD_dpath)
            mid = int(row['mid'])
            if mid_madd3[mid] not in lv_dh_madd[lv][dow, hour]:
                continue
            if (day, dow, hour) not in lv_ddh_mules[lv]:
                lv_ddh_mules[lv][day, dow, hour] = set()
            lv_ddh_mules[lv][day, dow, hour].add(mid)
            fpath = opath.join(trajBD_dpath, '%02d%02d-H%02d-W%d.csv' % (month, day, hour, dow))
            if not opath.exists(fpath):
                with open(fpath, 'w') as w_csvfile:
                    writer = csv.writer(w_csvfile, lineterminator='\n')
                    new_header = ['month', 'day', 'dow', 'hour', 'epoch',
                                  'mid', 'absent', 'visitedLocs']
                    writer.writerow(new_header)
            new_row = [month, day, dow, hour, epoch,
                       mid, 1 if row['prevHourLoc'] == 'X' else 0, row['visitedLocs']]
            with open(fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)
    #
    for lv in TARGET_LVS:
        dh_mules_fpath = opath.join(month_dpath, '__M%d-%s-muleDH.csv' % (month, lv))
        with open(dh_mules_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['day', 'dow', 'hour', 'numMules', 'mules']
            writer.writerow(new_header)
            for day, dow, hour in lv_ddh_mules[lv]:
                writer.writerow([day, dow, hour,
                                 len(lv_ddh_mules[lv][day, dow, hour]), list(lv_ddh_mules[lv][day, dow, hour])])


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


def init_experiments():
    exp_dpath = opath.join('z_data', '_experiments')
    __mid_madd = []
    for month in range(2, 4):
        month_dpath = get_base_dpath(month)
        muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
        with open(muleID_fpath, 'rb') as fp:
            _, mid_madd = pickle.load(fp)
            __mid_madd.append(mid_madd)
    mid_madd2, mid_madd3 = __mid_madd
    #
    timeHorizon = get_timeHorizon()
    for lv in TARGET_LVS:
        if lv == 'Lv2':
            continue
        dh_madd_ab_p_kbl = {}
        lv_dpath = opath.join(exp_dpath, lv)
        if not opath.exists(lv_dpath):
            os.mkdir(lv_dpath)
        p_dpath = opath.join(lv_dpath, 'p_kmbl')
        if not opath.exists(p_dpath):
            os.mkdir(p_dpath)
        epochs, bids, pls = set(), set(), set()
        for dt in timeHorizon:
            dh = (dt.weekday(), dt.hour)
            if dh not in dh_madd_ab_p_kbl:
                dh_madd_ab_p_kbl[dh] = {}
                month = 2
                m2_p_fpath = reduce(opath.join, [get_base_dpath(month), 'M%d-%s' % (month, lv),
                              'arr_p_kmbl', 'W%d-H%02d.csv' % (dt.weekday(), dt.hour)])
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
            m3_p_fpath = opath.join(p_dpath, 'p_kmbl-%02d%02d-H%02d.csv' % (dt.month, dt.day, dt.hour))
            with open(m3_p_fpath, 'w') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                new_header = ['day', 'dow', 'hour', 'epoch', 'mid', 'bid', 'pl', 'p_kmbl']
                writer.writerow(new_header)
            #
            madd_ab_p_kbl = dh_madd_ab_p_kbl[dh]
            trajByDay_fpath = reduce(opath.join, [get_base_dpath(dt.month), 'M%d-%s' % (dt.month, lv),
             'trajByDay', '%02d%02d-H%02d-W%d.csv' % (dt.month, dt.day, dt.hour, dt.weekday())])
            mid0_mid1 = {}
            with open(trajByDay_fpath) as r_csvfile:
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


if __name__ == '__main__':
    # aggregate_indiTraj(2)
    # gen_indiCouting(2)
    # gen_p_kmbl()
    # arrange_p_kmbl()
    # arrange_trajByDay()
    init_experiments()



