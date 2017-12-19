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



floor = 'Lv4'
numGeneration = 100
numPopulation = 50
numOffsprings = int(numPopulation * 0.8)
probCrossover = 0.5
probMutation = 0.5

maProb_dpath = opath.join('z_data', 'maRes-%s-G(%d)-P(%d)-O(%d)-pC(%.2f)-pM(%.2f)' %
                          (floor, numGeneration, numPopulation, numOffsprings, probCrossover, probMutation))
ifpath = opath.join(maProb_dpath, 'date.pkl')


def run():
    with open(ifpath, 'rb') as fp:
        inputs, bid_index = pickle.load(fp)





if __name__ == '__main__':
    run()