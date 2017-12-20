import os.path as opath
import os, fnmatch
import csv
import numpy as np
import matplotlib.pyplot as plt

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

FIGSIZE = (8, 6)
_fontsize = 14
yLabels = {'obj1': 'Obj1',
           'obj2': 'Obj2',
           'ratioUnCoveredBK': ''}

def numMules():
    floor = 'Lv2'
    res_fpath = opath.join('z_data', 'res-%s-FL%d.csv' % (floor, 0))
    times, measures = [], []
    aMeasure = []
    with open(res_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            yyyymmdd = row['date']
            mm = yyyymmdd[len('yyyymm'):]
            hour = int(row['hour'])
            times.append('Mar.%s H%02d' % (mm, hour))
            aMeasure.append(int(row['numMules2']))
    measures.append(aMeasure)
    xticks_index, xticks_label = [], []
    for i, yyyymmddhh in enumerate(times):
        if 'H09' in yyyymmddhh:
            xticks_index.append(i)
            xticks_label.append(yyyymmddhh)
    #
    floor = 'Lv4'
    res_fpath = opath.join('z_data', 'res-%s-FL%d.csv' % (floor, 0))
    aMeasure = []
    with open(res_fpath) as r_csvfile:
        reader = csv.DictReader(r_csvfile)
        for row in reader:
            aMeasure.append(int(row['numMules2']))
    measures.append(aMeasure)

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
    img_ofpath = 'numMules.pdf'
    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)


def objectivs_sim():
    floor = 'Lv2'
    ma_prefix = 'Lv2-G(50)-P(50)-O(40)-pC(0.50)-pM(0.50)'
    #
    # mea, _ylim, legendLoc = 'obj1', (700, 1005), 'lower left'
    # mea, _ylim, legendLoc = 'obj2', (-2, 65), 'upper right'
    # mea, _ylim, legendLoc = 'obj2', None, 'upper center'
    # mea, _ylim, legendLoc = 'ratioUnCoveredBK', (-0.01, 0.1), 'upper right'
    mea, _ylim, legendLoc = 'ratioUnCoveredBK', None, 'upper right'
    times, measures = [], []
    #
    # Fixed power levels
    #
    for l in range(3):
        res_fpath = opath.join('z_data', 'res-%s-FL%d.csv' % (floor, l))
        aMeasure = []
        with open(res_fpath) as r_csvfile:
            reader = csv.DictReader(r_csvfile)
            for row in reader:
                if l == 0:
                    yyyymmdd = row['date']
                    mm = yyyymmdd[len('yyyymm'):]
                    hour = int(row['hour'])
                    times.append('Mar.%s H%02d' % (mm, hour))
                aMeasure.append(float(row[mea]))
        measures.append(aMeasure)
    #
    # MA
    #
    res_fpath = opath.join('z_data', 'res-%s.csv' % ma_prefix)
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

    plt.legend(['FL%d' % l for l in range(3)] + ['MA'], ncol=1, loc=legendLoc, fontsize=_fontsize)
    plt.xticks(xticks_index, xticks_label, rotation=20)
    ax.tick_params(axis='both', which='major', labelsize=_fontsize)

    plt.ylim(_ylim)
    img_ofpath = '%s-%s.pdf' % (mea, ma_prefix)
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

    plt.plot(range(len(xs)), ys, color='black', linestyle=':')

    plots, labels = [], []

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
        p = plt.scatter(xs, ys, marker=mlists[i], s=70)
        plots += [p]
        labels += ['G%d' % Gs[i]]
    plt.legend(plots, labels, loc='lower right', ncol=1, fontsize=_fontsize, scatterpoints=1)



    plt.xticks(xticks_index, xticks_lable)

    plt.xlim((-1, 36))


    img_ofpath = 'evolution.pdf'
    plt.savefig(img_ofpath, bbox_inches='tight', pad_inches=0)





if __name__ == '__main__':
    numMules()
    # objectivs_sim()
    # evolution()