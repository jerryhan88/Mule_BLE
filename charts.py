import os.path as opath
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import csv
import pickle
from functools import reduce
#


_rgb = lambda r, g, b: (r / float(255), g / float(255), b / float(255))
clists = (
    'blue', 'green', 'red', 'magenta', 'black', 'cyan',
    _rgb(255, 165, 0), _rgb(238, 130, 238), _rgb(255, 228, 225),  # orange, violet, misty rose
    _rgb(127, 255, 212),  # aqua-marine
    'yellow',
    _rgb(220, 220, 220), _rgb(255, 165, 0),  # gray, orange
    'black'
)
mlists = (
    'o',  # circle
    '^',  # triangle_up
    'D',  # diamond
    '*',  # star
    '8',  # octagon


    'v',  #    triangle_down

    '<',  #    triangle_left
    '>',  #    triangle_right
    's',  #    square
    'p',  #    pentagon

    '+',  #    plus
    'x',  #    x

    'h',  #    hexagon1
    '1',  #    tri_down
    '2',  #    tri_up
    '3',  #    tri_left
    '4',  #    tri_right

    'H',  #    hexagon2
    'd',  #    thin_diamond
    '|',  #    vline
    '_',  #    hline
    '.',  #    point
    ',',  #    pixel

    '8',  #    octagon
    )

ltype = ['--', '-']

FIGSIZE = (8, 6)
FIGSIZE2 = (8, 4)

_fontsize = 14
yLabels = {'obj1': 'Obj1',
           'obj2': 'Obj2',
           'ratioUnCoveredBK': ''}


id_dow = {i: dow for i, dow in enumerate(['Mon.', 'Tue.', 'Wed.', 'Thr.', 'Fri.'])}


def numMules():
    times, measures = [], []
    for i, lv in enumerate(['Lv2', 'Lv4']):
        res_fpath = reduce(opath.join, ['z_data', '_experiments', lv, 'FL', 'res-FL%d.csv' % 0])
        aMeasure = []
        with open(res_fpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                if i == 0:
                    yyyymmdd = row['date']
                    year = int(yyyymmdd[:-len('mmdd')])
                    month = int(yyyymmdd[len('yyyy'):-len('dd')])
                    day = int(yyyymmdd[len('yyyymm'):])
                    hour = int(row['hour'])
                    times.append('%s H%02d' % (id_dow[datetime.datetime(year, month, day).weekday()], hour))
                aMeasure.append(int(row['numMules']))
        measures.append(aMeasure)
    xticks_index, xticks_label = [], []
    for i, yyyymmddhh in enumerate(times):
        if 'H09' in yyyymmddhh:
            xticks_index.append(i)
            xticks_label.append(yyyymmddhh)
    #
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    # ax.set_xlabel('Time', fontsize=_fontsize)
    # ax.set_ylabel(yLabels[mea], fontsize=_fontsize)
    for i, y in enumerate(measures):
        plt.plot(range(len(times)), y, color=clists[i], marker=mlists[i])

    plt.legend(['Lv2', 'Lv4'], ncol=1, loc='upper left', fontsize=_fontsize)
    plt.xticks(xticks_index, xticks_label, rotation=20)
    ax.tick_params(axis='both', which='major', labelsize=_fontsize)

    # plt.ylim(_ylim)
    img_ofpath = opath.join('_charts', 'numMules.pdf')
    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)


def objectivs_sim():
    lv = 'Lv2'
    # lv = 'Lv4'
    ma_prefix = 'G(50)-P(100)-O(80)-pC(0.50)-pM(0.50)'
    #
    # mea, _ylim, legendLoc = 'obj1', (700, 1005), 'lower left'
    # mea, _ylim, legendLoc = 'obj2', (-2, 130), 'upper right'
    # mea, _ylim, legendLoc = 'obj2', None, 'upper center'
    # mea, _ylim, legendLoc = 'ratioUnCoveredBK', (-0.01, 0.1), 'upper right'
    mea, _ylim, legendLoc = 'ratioUnCoveredBK', None, 'upper right'
    times, measures = [], []
    #
    # Fixed power levels
    #
    for l in range(3):
        res_fpath = reduce(opath.join, ['z_data', '_experiments', lv, 'FL', 'res-FL%d.csv' % l])
        aMeasure = []
        with open(res_fpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                if l == 0:
                    yyyymmdd = row['date']
                    hour = int(row['hour'])
                    # mm = yyyymmdd[len('yyyymm'):]
                    # times.append('Mar.%s H%02d' % (mm, hour))



                    times.append('%s H%02d' % (id_dow[int(row['dow'])], hour))

                aMeasure.append(float(row[mea]))
        measures.append(aMeasure)
    #
    # MA
    #
    res_fpath = reduce(opath.join, ['z_data', '_experiments', lv, 'res-%s.csv' % ma_prefix])
    aMeasure = []
    auxiliaryLines = [[], []]
    with open(res_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            mean_v = float(row[mea])
            std_v = float(row['std_%s' % mea])
            aMeasure.append(mean_v)
            auxiliaryLines[0].append(mean_v + std_v)
            auxiliaryLines[1].append(mean_v - std_v)
    measures.append(aMeasure)
    xticks_index, xticks_label = [], []
    for i, yyyymmddhh in enumerate(times):
        if 'H09' in yyyymmddhh:
            xticks_index.append(i)
            xticks_label.append(yyyymmddhh)
    #
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    # ax.set_xlabel('Time', fontsize=_fontsize)
    # ax.set_ylabel(yLabels[mea], fontsize=_fontsize)
    for i, y in enumerate(measures):
        plt.plot(range(len(times)), y, color=clists[i], marker=mlists[i])
    if mea == 'obj1':
        for y in auxiliaryLines:
            plt.plot(range(len(times)), y, color=clists[i], linestyle=':')

    plt.legend(['FL%d' % (l + 1) for l in range(3)] + ['MA'], ncol=1, loc=legendLoc, fontsize=_fontsize)
    plt.xticks(xticks_index, xticks_label, rotation=20)
    ax.tick_params(axis='both', which='major', labelsize=_fontsize)

    plt.ylim(_ylim)
    img_ofpath = opath.join('_charts', '%s-%s-%s.pdf' % (lv, mea, ma_prefix))

    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)


def evolution():
    '''
    _MA-Lv4-G(50)-P(50)-O(40)-pC(0.50)-pM(0.50)-R0
    evol-20170306H11
    '''
    ys = [806.5723802, 812.9617421, 812.9617421,
         816.1117387, 816.1117387, 816.1117387, 816.1117387, 816.1117387, 816.1117387,
         816.1117387, 816.1117387, 816.1117387, 816.1117387, 816.1117387, 816.1117387,
         816.1117387, 816.1117387, 816.1117387, 816.1117387, 816.1117387, 818.2713155,
         818.2713155, 818.2713155, 818.2713155, 818.2713155, 818.2713155, 818.2713155,
         818.2713155, 818.2713155, 818.2713155, 818.2713155, 818.2713155, 818.2713155,
         818.2713155, 818.2713155]
    xs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
         21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]

    xticks_index, xticks_lable = [], []
    for x in xs:
        if x % 5 == 0:
            xticks_index.append(x - 1)
            xticks_lable.append(x)
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    ax.set_xlabel('Number of selected mules', fontsize=_fontsize)
    ax.set_ylabel('Minimum battery power', fontsize=_fontsize)

    labels = []
    plt.plot(range(len(xs)), ys, color='black', linestyle=':')
    labels += ['App.']



    Gs = [1, 13, 30, 45]
    yss = [[803.4223836008993, 806.5723802265991, 812.9617420807992, 818.2713155254993],
           [806.5723802265991, 812.9617420807992, 816.1117387064991, 818.2713155254993],
           [806.5723802265991, 816.1117387064991, 818.2713155254993],
           [816.1117387064991, 818.2713155254993]]
    xss = [[19, 21, 22, 31],
           [18, 19, 27, 28],
           [16, 17, 22],
           [12, 18]]



    for i in range(len(xss)):
        ys, xs = yss[i], xss[i]
        # p = plt.scatter(xs, ys, marker=mlists[i], s=70, c=clists[i])

        plt.plot(xs, ys, color=clists[i], marker=mlists[i])

        # labels += ['G%d' ]
        labels += ['G%02d' % Gs[i]]
    plt.legend(labels, ncol=1, loc='lower right', fontsize=_fontsize)
    plt.xticks(xticks_index, xticks_lable)
    ax.tick_params(axis='both', which='major', labelsize=_fontsize)

    plt.xlim((-1, 36))

    img_ofpath = 'evolution.pdf'
    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)



def boxPlots():
    dpath = opath.join('z_data', 'experiment2')
    fns = ['summary-G50-S1.csv', 'summary-G50-S0.csv',
           'summary-G100-S1.csv', 'summary-G100-S0.csv']


    for m in ['obj1', 'obj2', 'comTime']:
        data = []
        for fn in fns:
            df = pd.read_csv(opath.join(dpath, fn))
            data.append(df[m])
            # obj2s.append(df[])
            # comTimes.append(df[])

        fig = plt.figure(figsize=FIGSIZE2)
        ax = fig.add_subplot(111)
        # ax.set_xlabel('Parameter setting', fontsize=_fontsize)
        ax.tick_params(axis='both', which='major', labelsize=_fontsize)
        medianprops = dict(linestyle='-', linewidth=2.0)
        boxprops = dict(linestyle='--', linewidth=1.0)
        plt.boxplot(data, boxprops=boxprops, medianprops=medianprops)

        img_ofpath = 'boxplot_%s.pdf' % m
        plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)


def chart_Markov():
    from beaconLayout import TARGET_LVS
    comp_dpath = reduce(opath.join, ['..', '_data', 'Mule_BLE', '_comparision'])
    for lv in TARGET_LVS:
        error_fpath = opath.join(comp_dpath, '_error-%s.pkl' % lv)
        with open(error_fpath, 'rb') as fp:
            error_xMarkov, error_Markov = pickle.load(fp)
        # error_xMarkov, error_Markov = map(np.array, [error_xMarkov, error_Markov])
        #
        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)
        for i, error in enumerate([error_xMarkov, error_Markov]):
            error = np.sort(np.array(error))
            yvals = np.arange(len(error)) / float(len(error) - 1)
            plt.plot(error, yvals, ltype[i], color=clists[i])
        # plt.legend(['%d-Step' % i for i in range(2)], ncol=1, fontsize=_fontsize)
        ax.tick_params(axis='both', which='major', labelsize=_fontsize)
        plt.ylim((0.0, 1.0))
        img_ofpath = opath.join('_charts', '%s-errorCDF.pdf' % lv)
        plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)
        plt.close()
        #
        fig = plt.figure(figsize=FIGSIZE)
        ax = fig.add_subplot(111)
        for i, error in enumerate([error_xMarkov, error_Markov]):
            error = np.sort(np.array(error))
            yvals = np.arange(len(error)) / float(len(error) - 1)
            plt.plot(error, yvals, ltype[i], color=clists[i])
        plt.legend(['0th-order', '1st-order'], ncol=1, loc='upper left', fontsize=_fontsize + 6)
        ax.tick_params(axis='both', which='major', labelsize=_fontsize + 6)
        plt.xlim((-0.02, 0.33))
        plt.ylim((0.78, 0.88))
        img_ofpath = opath.join('_charts', '%s-errorCDF_zoom.pdf' % lv)
        plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)
        plt.close()




def solutionChoice():
    FIGSIZE = (6, 6)

    from experiments import exp_dpath
    numEpoch, lv = 4, 'Lv4'
    ma_prefix = 'G(50)-P(100)-O(80)-pC(0.50)-pM(0.50)'
    #
    # mea, _ylim, legendLoc = 'obj1', (700, 1005), 'lower left'
    mea, _ylim, legendLoc = 'obj2', (0, 30), 'upper right'
    # mea, _ylim, legendLoc = 'ratioUnCoveredBK', None, 'upper right'
    #
    times, measures = [], []
    res_dpath = reduce(opath.join, [exp_dpath, 'epoch%d' % numEpoch, lv, 'results'])
    for i, ma_id in enumerate(['MA1', 'MA0']):
        res_fpath = opath.join(res_dpath, 'E%d-res-%s-%s.csv' % (numEpoch, ma_id, ma_prefix))
        aMeasure = []
        with open(res_fpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                if i == 0:
                    hour = int(row['hour'])
                    times.append('%s H%02d' % (id_dow[int(row['dow'])], hour))
                aMeasure.append(float(row[mea]))
        measures.append(aMeasure)



    xticks_index, xticks_label = [], []
    for i, yyyymmddhh in enumerate(times):
        if 'H09' in yyyymmddhh:
            xticks_index.append(i)
            xticks_label.append(yyyymmddhh)
    #
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    # ax.set_xlabel('Time', fontsize=_fontsize)
    # ax.set_ylabel(yLabels[mea], fontsize=_fontsize)
    for i, y in enumerate(measures):
        plt.plot(range(len(times)), y, color=clists[3 + i], marker=mlists[3 + i])
    plt.legend(['MA-Random', 'MA-Small'], ncol=1, loc=legendLoc, fontsize=_fontsize)
    plt.xticks(xticks_index, xticks_label, rotation=20)
    ax.tick_params(axis='both', which='major', labelsize=_fontsize)

    plt.ylim(_ylim)
    img_ofpath = opath.join('_charts', 'SolChoice-%s-%s.pdf' % (lv, mea))

    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)





if __name__ == '__main__':
    # numMules()
    # objectivs_sim()
    # evolution()
    # boxPlots()
    chart_Markov()
    # solutionChoice()