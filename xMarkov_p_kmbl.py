import os.path as opath
import os
import csv
import pickle
#
from dataProcessing import get_base_dpath
from dataProcessing import get_bzDist, get_plCovLD
from dataProcessing import PL_RANGE, TARGET_LVS


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


if __name__ == '__main__':
    # gen_p_kmbl_xMarkov()
    arrange_p_kmbl_xMarkov()