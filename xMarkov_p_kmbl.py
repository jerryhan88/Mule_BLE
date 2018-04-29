import os.path as opath
import os
import csv
import pickle
from functools import reduce
#
from dataProcessing import get_base_dpath
from dataProcessing import get_bzDist, get_plCovLD
from dataProcessing import PL_RANGE, TARGET_LVS
from dataProcessing import get_timeHorizon


def gen_p_kmbl_xMarkov():
    month = 2
    month_dpath = get_base_dpath(month)
    indiCouting_fpath = opath.join(month_dpath, 'M%d-aggIndiCouting.csv' % month)
    lvMid_dhe_nRecords, mid_dhe_nVisitedLocs = {}, {}
    with open(indiCouting_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            lv = row['lv']
            lv_dpath = opath.join(month_dpath, 'M%d-%s' % (month, lv))
            p_dpath = opath.join(lv_dpath, 'p_kmbl')
            if not opath.exists(p_dpath):
                os.mkdir(p_dpath)
            mid = row['mid']
            k0 = (lv, mid)
            if k0 not in lvMid_dhe_nRecords:
                lvMid_dhe_nRecords[k0] = {}
                mid_dhe_nVisitedLocs[k0] = {}
            dow, hour, epoch, absent = [row[cn] for cn in ['dow', 'hour', 'epoch', 'absent']]
            k1 = (dow, hour, epoch)
            if k1 not in lvMid_dhe_nRecords[k0]:
                lvMid_dhe_nRecords[k0][k1] = 0
                mid_dhe_nVisitedLocs[k0][k1] = {}
            nReocrds, nVisitedLocs = [eval(row[cn]) for cn in ['nReocrds', 'nVisitedLocs']]
            lvMid_dhe_nRecords[k0][k1] += nReocrds
            for locID, nVisit in nVisitedLocs.items():
                if locID not in mid_dhe_nVisitedLocs[k0][k1]:
                    mid_dhe_nVisitedLocs[k0][k1][locID] = 0
                mid_dhe_nVisitedLocs[k0][k1][locID] += nVisit
    #
    bids, plCovLD = {}, {}
    for lv, mid in lvMid_dhe_nRecords:
        lv_dpath = opath.join(month_dpath, 'M%d-%s' % (month, lv))
        p_dpath = opath.join(lv_dpath, 'p_kmbl_xMarkov')
        if not opath.exists(p_dpath):
            os.mkdir(p_dpath)
        _mid = 'm%s' % mid
        fpath = opath.join(p_dpath, 'M%d-%s-%s.csv' % (month, lv, _mid))
        if not opath.exists(fpath):
            with open(fpath, 'w') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                new_header = ['lv', 'mid', 'dow', 'hour', 'epoch',
                              'bid', 'pl', 'p_kmbl_xMarkov',
                              'nReocrds', 'withinLocs']
                writer.writerow(new_header)
        if lv not in bids:
            bzDist = get_bzDist(lv)
            bids[lv] = list(bzDist.keys())
            plCovLD[lv] = get_plCovLD(lv)
        dhe_nRecords = lvMid_dhe_nRecords[lv, mid]
        dhe_nVisitedLocs = mid_dhe_nVisitedLocs[lv, mid]
        for dow, hour, epoch in dhe_nRecords:
            nRecords = dhe_nRecords[dow, hour, epoch]
            nVisitedLocs = dhe_nVisitedLocs[dow, hour, epoch]
            for bid, bidLong in enumerate(bids[lv]):
                for pl in range(len(PL_RANGE)):
                    visitedLocs = set(nVisitedLocs.keys())
                    coveringLD = set(plCovLD[lv][bidLong, pl])
                    intersectLocs = visitedLocs.intersection(coveringLD)
                    if intersectLocs:
                        _p_kmbl = 1
                        for loc in intersectLocs:
                            _p_kmbl *= (1 - (int(nVisitedLocs[loc]) / float(nRecords)))
                            if _p_kmbl == 0.0:
                                break
                        p_kmbl = 1 - _p_kmbl
                    else:
                        p_kmbl = 0.0
                    new_row = [lv, mid, dow, hour, epoch,
                               bid, pl, p_kmbl, nRecords, dict((loc, nVisitedLocs[loc]) for loc in intersectLocs)]
                    with open(fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow(new_row)


def arrange_p_kmbl_xMarkov():
    month = 2
    month_dpath = get_base_dpath(month)

    for dname in os.listdir(month_dpath):
        if not opath.isdir(opath.join(month_dpath, dname)):
            continue
        _, lv = dname.split('-')
        if lv not in TARGET_LVS:
            continue
        lv_dpath = opath.join(month_dpath, dname)
        p0_dpath = opath.join(lv_dpath, 'p_kmbl_xMarkov')
        p1_dpath = opath.join(lv_dpath, 'arr_p_kmbl_xMarkov')
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
                            new_header = ['lv', 'dow', 'hour', 'epoch', 'mid', 'bid', 'pl', 'p_kmbl']
                            writer.writerow(new_header)
                    epoch, mid, bid, pl = [row[cn] for cn in ['epoch', 'mid', 'bid', 'pl']]
                    p_kmbl = eval(row['p_kmbl_xMarkov'])
                    if (dow, hour) not in dh_mules:
                        dh_mules[dow, hour] = set()
                        dh_p_kmbl[dow, hour] = {}
                    dh_mules[dow, hour].add(mid)
                    dh_p_kmbl[dow, hour][epoch, mid, bid, pl] = p_kmbl
                    #
                    new_row = [lv, dow, hour, epoch, mid, bid, pl, p_kmbl]
                    with open(fpath, 'a') as w_csvfile:
                        writer = csv.writer(w_csvfile, lineterminator='\n')
                        writer.writerow(new_row)
        dh_mules_fpath = opath.join(month_dpath, '__M%d-%s-muleDH_xMarkov.csv' % (month, lv))
        with open(dh_mules_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['dow', 'hour', 'numMules', 'mules']
            writer.writerow(new_header)
            for dow, hour in dh_mules:
                writer.writerow([dow, hour, len(dh_mules[dow, hour]), list(dh_mules[dow, hour])])
        p_kmbl_fpath = opath.join(month_dpath, '_M%d-%s-p_kmbl_xMarkov.pkl' % (month, lv))
        with open(p_kmbl_fpath, 'wb') as fp:
            pickle.dump(dh_p_kmbl, fp)



def comparison_summary():
    __mid_madd = []
    for month in range(2, 4):
        month_dpath = get_base_dpath(month)
        muleID_fpath = opath.join(month_dpath, '_muleID-M%d.pkl' % month)
        with open(muleID_fpath, 'rb') as fp:
            _, mid_madd = pickle.load(fp)
            __mid_madd.append(mid_madd)
    mid_madd2, mid_madd3 = __mid_madd
    #
    comp_dpath = opath.join('z_data', '_comparision')
    timeHorizon = get_timeHorizon()
    for lv in TARGET_LVS:
        error_xMarkov, error_Markov = [], []
        error_fpath = opath.join(comp_dpath, '_error-%s.pkl' % lv)
        bid_bidLong = {}
        for bid, bidLong in enumerate(get_bzDist(lv)):
            bid_bidLong[bid] = bidLong
        plCovLD = get_plCovLD(lv)
        #
        epochs, bids, pls = set(), set(), set()
        for dt in timeHorizon:
            comp_fpath = opath.join(comp_dpath, '%s-%d%02d%02dH%02d-comparision.csv' % (lv,
                                                   dt.year, dt.month, dt.day, dt.hour))
            with open(comp_fpath, 'w') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                new_header = ['day', 'dow', 'hour', 'epoch', 'mid', 'bid', 'pl',
                              'visitedLocs', 'diff',
                              'p_kmbl_xMarkov', 'p_kmbl_Markov', 'covered',
                              'error_xMarkov', 'error_Markov']
                writer.writerow(new_header)
            month = 2
            madd_ab_p_kbl = {}
            madd_p_kbl = {}
            #
            m2_p1_fpath = reduce(opath.join, [get_base_dpath(month), 'M%d-%s' % (month, lv),
                          'arr_p_kmbl', 'W%d-H%02d.csv' % (dt.weekday(), dt.hour)])
            with open(m2_p1_fpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    mid0 = int(row['mid'])
                    madd = mid_madd2[mid0]
                    if madd not in madd_ab_p_kbl:
                        madd_ab_p_kbl[madd] = {}
                    absent, epoch, bid, pl = [int(row[cn]) for cn in ['absent', 'epoch', 'bid', 'pl']]
                    if absent not in madd_ab_p_kbl[madd]:
                        madd_ab_p_kbl[madd][absent] = {}
                    madd_ab_p_kbl[madd][absent][epoch, bid, pl] = eval(row['p_kmbl'])
                    epochs.add(epoch)
                    bids.add(bid)
                    pls.add(pl)
            #
            m2_p0_fpath = reduce(opath.join, [get_base_dpath(month), 'M%d-%s' % (month, lv),
                                              'arr_p_kmbl_xMarkov', 'W%d-H%02d.csv' % (dt.weekday(), dt.hour)])
            with open(m2_p0_fpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    mid0 = int(row['mid'])
                    madd = mid_madd2[mid0]
                    if madd not in madd_p_kbl:
                        madd_p_kbl[madd] = {}
                    epoch, bid, pl = [int(row[cn]) for cn in ['epoch', 'bid', 'pl']]
                    madd_p_kbl[madd][epoch, bid, pl] = eval(row['p_kmbl'])
            #
            trajByDay_fpath = reduce(opath.join, [get_base_dpath(dt.month), 'M%d-%s' % (dt.month, lv),
             'trajByDay', '%02d%02d-H%02d-W%d.csv' % (dt.month, dt.day, dt.hour, dt.weekday())])
            m3_madd_k_ab_traj = {}
            madd_mid = {}
            with open(trajByDay_fpath) as r_csvfile:
                reader = csv.DictReader(r_csvfile)
                for row in reader:
                    mid0, epoch = [int(row[cn]) for cn in ['mid', 'epoch']]
                    madd = mid_madd3[mid0]
                    if mid0 not in madd_mid:
                        madd_mid[madd] = len(madd_mid)
                    absent = int(row['absent'])
                    m3_madd_k_ab_traj[madd, epoch] = (absent, eval(row['visitedLocs']))
            for madd, epoch in m3_madd_k_ab_traj:
                absent, visitedLocs = m3_madd_k_ab_traj[madd, epoch]
                for bid in bids:
                    for pl in pls:
                        try:
                            p_xMarkov = madd_p_kbl[madd][epoch, bid, pl]
                            p_Markov = madd_ab_p_kbl[madd][absent][epoch, bid, pl]
                        except KeyError:
                            continue
                        covered = 1 if set(plCovLD[bid_bidLong[bid], pl]).intersection(visitedLocs) else 0
                        error0 = abs(covered - p_xMarkov)
                        error1 = abs(covered - p_Markov)
                        error_xMarkov.append(error0)
                        error_Markov.append(error1)
                        #
                        with open(comp_fpath, 'a') as w_csvfile:
                            writer = csv.writer(w_csvfile, lineterminator='\n')
                            writer.writerow([dt.day, dt.weekday(), dt.hour,
                                   epoch, madd_mid[madd], bid, pl,
                                   visitedLocs, p_xMarkov - p_Markov,
                                   p_xMarkov, p_Markov, covered,
                                             error0, error1])
        with open(error_fpath, 'wb') as fp:
            pickle.dump([error_xMarkov, error_Markov], fp)


import numpy as np
import matplotlib.pyplot as plt

def cdf_chart():
    comp_dpath = opath.join('z_data', '_comparision')
    for lv in TARGET_LVS:
        error_fpath = opath.join(comp_dpath, '_error-%s.pkl' % lv)
        with open(error_fpath, 'rb') as fp:
            error_xMarkov, error_Markov = pickle.load(fp)
        error_xMarkov, error_Markov = map(np.array, [error_xMarkov, error_Markov])
    sorted_error_xMarkov = np.sort(error_xMarkov)
    yvals=np.arange(len(sorted_error_xMarkov)) / float(len(sorted_error_xMarkov) - 1)
    plt.plot(sorted_error_xMarkov,yvals)
    
    sorted_error_Markov = np.sort(error_Markov)
    yvals=np.arange(len(sorted_error_Markov)) / float(len(sorted_error_Markov) - 1)
    plt.plot(sorted_error_Markov,yvals)
    
    plt.show()
    
    
    y, binEdges=np.histogram(sorted_error_xMarkov,bins=10000)
    bincenters = 0.5 * (binEdges[1:]+binEdges[:-1])
    plt.plot(bincenters,y / len(sorted_error_xMarkov),'-')
    plt.show()
    
    
    y, binEdges=np.histogram(sorted_error_Markov,bins=100)
    bincenters = 0.5 * (binEdges[1:]+binEdges[:-1])
    plt.plot(bincenters,y / len(sorted_error_Markov),'-')
    plt.show()


if __name__ == '__main__':
    # gen_p_kmbl_xMarkov()
    # arrange_p_kmbl_xMarkov()
    comparison_summary()