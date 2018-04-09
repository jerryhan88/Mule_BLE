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


HOUR_9AM_6PM = [h for h in range(9, 18)]
MON, TUE, WED, THR, FRI, SAT, SUN = range(7)
WEEK_DAYS = [MON, TUE, WED, THR, FRI]
N_TIMESLOT = 4
Intv = 60 / N_TIMESLOT
PL_RANGE = [3, 7, 10]
PL_CUNSUME = [1, 6.3095734447, 15.8489319246]
MIN_BATTERY_POWER, MAX_BATTERY_POWER = 980, 1000


landmarks_fpath = opath.join('z_data', 'Landmarks.xlsx')
beacons_fpath = opath.join('z_data', 'BeaconLocation.xlsx')
rawTraj2_fpath = opath.join('z_data', 'location_archival_2017_2_1.csv.gz')
rawTraj3_fpath = opath.join('z_data', 'location_archival_2017_3_1.csv.gz')


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


def get_base_dpath(month):
    if month == 2:
        base_dpath = opath.join('z_data', 'M2')
    else:
        assert month == 3
        base_dpath = opath.join('z_data', 'M3')
    if not opath.exists(base_dpath):
        os.mkdir(base_dpath)
    return base_dpath


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
        indi_dpath = opath.join(dpath, '_indiDur')
        print(indi_dpath)
        if opath.exists(indi_dpath):
            shutil.rmtree(indi_dpath)
        os.mkdir(indi_dpath)
        for fn in sorted([fn for fn in os.listdir(dpath) if fn.endswith('.csv')]):
            lv = fn.split('-')[1]
            if not fn.endswith('.csv'):
                continue
            mule_lastTimeLoc = {}
            with open(opath.join(dpath, fn)) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    t1 = datetime.datetime.fromtimestamp(time.mktime(time.strptime(row['time'], "%Y-%m-%d %H:%M:%S")))
                    madd, loc1 = [row[cn] for cn in ['id', 'location']]
                    if madd not in mule_lastTimeLoc:
                        mule_lastTimeLoc[madd] = [t1, loc1]
                        continue
                    t0, loc0 = mule_lastTimeLoc[madd]
                    if loc1 == loc0:
                        continue
                    else:
                        fpath = opath.join(indi_dpath, 'M%d-%s-m%d.csv' % (month, lv, madd_mid[madd]))
                        if not opath.exists(fpath):
                            with open(fpath, 'w') as w_csvfile:
                                writer = csv.writer(w_csvfile, lineterminator='\n')
                                new_header = ['mid', 'fTime', 'tTime', 'duration', 'location']
                                writer.writerow(new_header)
                        with open(fpath, 'a') as w_csvfile:
                            writer = csv.writer(w_csvfile, lineterminator='\n')
                            writer.writerow([madd_mid[madd], t0, t1, (t1 - t0).seconds, loc0])
                        mule_lastTimeLoc[madd] = [t1, loc1]
    #
    lvs_dpath = [opath.join(month_dpath, dname) for dname in os.listdir(month_dpath) if opath.isdir(opath.join(month_dpath, dname))]
    ps = []
    for dpath in lvs_dpath:
        p = multiprocessing.Process(target=handle_lv_individual_duration, args=(dpath, ))
        ps.append(p)
        p.start()
    for p in ps:
        p.join()