import os.path as opath
import os, shutil
import multiprocessing
import gzip, csv, pickle
import datetime, time
import pandas as pd
from functools import reduce


HOUR_9AM_6PM = [h for h in range(9, 18)]
MON, TUE, WED, THR, FRI, SAT, SUN = range(7)
WEEK_DAYS = [MON, TUE, WED, THR, FRI]
LEAST_DAYS = 4
#
# Input file path
#
raw_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', '_raw'])
rawTraj2_fpath = opath.join(raw_dpath, 'location_archival_2017_2_1.csv.gz')
rawTraj3_fpath = opath.join(raw_dpath, 'location_archival_2017_3_1.csv.gz')
#
# Output directory path
#
md_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', 'muleDuration'])
if not opath.exists(md_dpath):
    os.mkdir(md_dpath)

get_dt = lambda tf_str: datetime.datetime.fromtimestamp(time.mktime(time.strptime(tf_str, "%Y-%m-%d %H:%M:%S")))


def month2LvDay(month):
    month_dpath = opath.join(md_dpath, 'M%d' % month)
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
            lv_dpath = opath.join(month_dpath, '%s' % lv)
            if not opath.exists(lv_dpath):
                os.mkdir(lv_dpath)
            fpath = opath.join(lv_dpath, 'MD-M%d-%s-%d%02d%02d.csv' % (month, lv, t.tm_year, t.tm_mon, t.tm_mday))
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
    muleID_fpath = reduce(opath.join, [md_dpath, 'M%d' % month, '_muleID-M%d.pkl' % month])
    with open(muleID_fpath, 'rb') as fp:
        madd_mid, mid_madd = pickle.load(fp)
    #
    def handle_lv_individual_duration(dpath):
        indi_dpath = opath.join(dpath, 'individual')
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
                fpath = opath.join(indi_dpath, 'MD-M%d-%s-m%d.csv' % (month, lv, madd_mid[madd]))
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
    month_dpath = reduce(opath.join, [md_dpath, 'M%d' % month])
    lvs_dpath = sorted([opath.join(month_dpath, dname) for dname in os.listdir(month_dpath) if opath.isdir(opath.join(month_dpath, dname))])
    ps = []
    for dpath in lvs_dpath:
        p = multiprocessing.Process(target=handle_lv_individual_duration, args=(dpath, ))
        ps.append(p)
        p.start()
    for p in ps:
        p.join()


def aggregate_indiDur(month):
    month_dpath = opath.join(md_dpath, 'M%d' % month)
    indiDur_fpath = opath.join(month_dpath, 'M%d-aggMuleDuration.csv' % month)
    #
    muleDayLv_duration = {}
    lvs_dpath = [opath.join(month_dpath, dname) for dname in os.listdir(month_dpath) if
                 opath.isdir(opath.join(month_dpath, dname))]
    mids, days, lvs = set(), set(), set()
    for lv_dpath in lvs_dpath:
        indi_dpath = opath.join(lv_dpath, 'individual')
        for fn in os.listdir(indi_dpath):
            if not fn.endswith('.csv'):
                continue
            lv = fn.split('-')[2]
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
    month_dpath = opath.join(md_dpath, 'M%d' % month)
    am_fpath = reduce(opath.join, [month_dpath, 'M%d' % month, '_activeMules-M%d.pkl' % month])
    indiDur_fpath = opath.join(month_dpath, 'M%d-aggMuleDuration.csv' % month)
    #
    df = pd.read_csv(indiDur_fpath)
    df = df.groupby(['mid', 'day']).sum()['duration'].reset_index()
    df = df.groupby(['mid']).count()['day'].to_frame('days').reset_index()
    df = df[(df['days'] > LEAST_DAYS)]
    active_mids = set(df['mid'])
    print("# active mules in Feb.: %d" % len(active_mids))
    with open(am_fpath, 'wb') as fp:
        pickle.dump(active_mids, fp)