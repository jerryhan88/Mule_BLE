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
numGeneration = 100
numPopulation = 50
numOffsprings = int(numPopulation * 0.8)
probCrossover = 0.5
probMutation = 0.5

maProb_dpath = opath.join('z_data', 'maRes-%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' %
                          (floor, numGeneration, numPopulation, numOffsprings, probCrossover, probMutation))
ifpath = opath.join(maProb_dpath, '20170303H12.pkl')
ofpath = opath.join(maProb_dpath, '_20170303H12.pkl')


def run():
    for fn in os.listdir(maProb_dpath):
        if not fnmatch.fnmatch(fn, '*.pkl'):
            continue


    os.listdir()


    with open(ifpath, 'rb') as fp:
        inputs, bid_index = pickle.load(fp)

    mo = order_mules(inputs)
    gh_objs = []
    for i in range(len(mo)):
        gh_objs.append(gh_run(inputs, mo[:i + 1]))

    print(gh_objs)
    # evolution = ma_run(inputs,
    #                      numGeneration, numPopulation, numOffsprings, probCrossover, probMutation, experiment2=True)
    # print()
    # print(evolution)












if __name__ == '__main__':
    run()