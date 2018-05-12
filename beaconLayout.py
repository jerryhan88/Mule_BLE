import os.path as opath
import os
import pickle
from math import sqrt
import networkx as nx
from xlrd import open_workbook
from functools import reduce

PL_RANGE = [3, 7, 10]
TARGET_LVS = {'Lv2', 'Lv4'}
#
# Input file path
#
raw_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', '_raw'])
beacons_fpath = opath.join(raw_dpath, 'BeaconLocation.xlsx')
landmarks_fpath = opath.join(raw_dpath, 'Landmarks.xlsx')
#
# Output directory path
#
bl_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'beaconLayout'])

if not opath.exists(bl_dpath):
    os.mkdir(bl_dpath)


def get_beacon2landmark(floor):
    beaconInfo_fpath = opath.join(bl_dpath, 'beaconInfo-%s.pkl' % floor)
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
    gridLayout_fpath = opath.join(bl_dpath, 'gridLayout-%s.pkl' % floor)
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
    bzDist_fpath = opath.join(bl_dpath, 'bzDist-%s.pkl' % floor)
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
    plCovLD_fpath = opath.join(bl_dpath, 'plCovLD-%s.pkl' % floor)
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
    lmPairSP_fpath = opath.join(bl_dpath, 'lmPairSP-%s.pkl' % floor)
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
    plCovTraj_fpath = opath.join(bl_dpath, 'plCovTraj-%s.pkl' % floor)
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