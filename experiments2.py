import os.path as opath
import pickle

prefix = 'memeticAlgorithm'
pyx_fn, c_fn = '%s.pyx' % prefix, '%s.c' % prefix
if opath.exists(c_fn):
    if opath.getctime(c_fn) < opath.getmtime(pyx_fn):
        from setup import cythonize; cythonize(prefix)
else:
    from setup import cythonize; cythonize(prefix)
from memeticAlgorithm import run as ma_run
from greedyHeuristic import run as gh_run
#
from problems import *


floor = 'Lv4'
numGeneration = 50
numPopulation = 50
numOffsprings = int(numPopulation * 0.8)
probCrossover = 0.5
probMutation = 0.5

maProb_dpath = opath.join('z_data', 'maRes-%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' %
                          (floor, numGeneration, numPopulation, numOffsprings, probCrossover, probMutation))


def run():
    for fn in os.listdir(maProb_dpath):
        if not fnmatch.fnmatch(fn, '*.pkl'):
            continue
        print(fn)
        prefix = fn[:-len('.pkl')]
        ifpath = opath.join(maProb_dpath, fn)
        with open(ifpath, 'rb') as fp:
            inputs, bid_index = pickle.load(fp)
        #
        gh_fpath = opath.join(maProb_dpath, '%s-GH.csv' % prefix)
        with open(gh_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['obj1', 'obj2']
            writer.writerow(new_header)
        mo = order_mules(inputs)
        gh_objs = []
        for i in range(len(mo)):
            new_row = list(gh_run(inputs, mo[:i + 1]))
            with open(gh_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)
        #
        ma_fpath = opath.join(maProb_dpath, '%s-MA.csv' % prefix)
        with open(gh_fpath, 'w') as w_csvfile:
            writer = csv.writer(w_csvfile, lineterminator='\n')
            new_header = ['generation', 'paretoFront']
            writer.writerow(new_header)
        evolution = ma_run(inputs,
                             numGeneration, numPopulation, numOffsprings, probCrossover, probMutation, experiment2=True)
        for i, objs in enumerate(evolution):
            objs = list(objs)
            objs.sort()
            new_row = [i + 1, objs]
            with open(gh_fpath, 'a') as w_csvfile:
                writer = csv.writer(w_csvfile, lineterminator='\n')
                writer.writerow(new_row)


if __name__ == '__main__':
    run()