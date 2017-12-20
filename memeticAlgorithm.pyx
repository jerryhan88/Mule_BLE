import random

class Individual(object):
    def __init__(self, inputs):
        self.inputs = inputs
        #
        self.g1, self.g2 = [], []
        self.obj1, self.obj2 = None, None

    def __repr__(self):
        return '|%s|%s|' % (''.join(['%d' % v for v in self.g1]), ''.join(['%d' % v for v in self.g2]))

    def init_gene(self):
        self.g1 = [random.randrange(len(self.inputs['L'])) for _ in range(len(self.inputs['B']))]
        self.g2 = [random.randrange(2) for _ in range(len(self.inputs['M']))]

    def evaluation(self):
        is_feasible = True
        min_rb = 1e400
        for b in self.inputs['B']:
            l = self.g1[b]
            rb = self.inputs['c_b'][b] - self.inputs['e_l'][l]
            if rb < min_rb:
                min_rb = rb
            for k in self.inputs['K']:
                xProb = 1
                for m in self.inputs['M']:
                    if self.g2[m] == 1:
                        xProb *= (1 - self.inputs['p_kmbl'][k, m, b, l])
                if 1 - xProb < self.inputs['R']:
                    is_feasible = False
                    break
        self.obj1 = min_rb
        self.obj2 = sum(self.g2) if is_feasible else len(self.inputs['M'])

    def clone(self):
        c = Individual(self.inputs)
        c.g1 = self.g1[:]
        c.g2 = self.g2[:]
        return c


def genPopulation(inputs, Np):
    population = []
    for _ in range(Np):
        ind = Individual(inputs)
        ind.init_gene()
        ind.evaluation()
        population.append(ind)
    return population


def cxInd(ind1, ind2):
    g1_halfSize = int(len(ind1.g1) / 2)
    ind1_g1 = ind1.g1[:g1_halfSize] + ind2.g1[g1_halfSize:]
    ind2_g1 = ind2.g1[:g1_halfSize] + ind1.g1[g1_halfSize:]
    #
    g2_halfSize = int(len(ind1.g2) / 2)
    ind1_g2 = ind1.g2[:g2_halfSize] + ind2.g2[g2_halfSize:]
    ind2_g2 = ind2.g2[:g2_halfSize] + ind1.g2[g2_halfSize:]
    #
    ind1.g1, ind2.g1 = ind1_g1, ind2_g1
    ind1.g2, ind2.g2 = ind1_g2, ind2_g2


def mutInd(ind):
    ind.g1[random.randrange(len(ind.g1))] = random.randrange(len(ind.inputs['L']))
    ind.g2[random.randrange(len(ind.g2))] = random.randrange(2)


def selInds(prevGen, newGen, N_p, ndSolSelection=False):
    cp = prevGen + newGen
    is_efficient = [True for _ in range(len(cp))]
    for i, ind1 in enumerate(cp):
        efficient = True
        for ind2 in cp:
            if ind1 == ind2:
                continue
            if ind1.obj1 <= ind2.obj1:
                if ind1.obj2 > ind2.obj2:
                    efficient = False
                    break
            if ind1.obj2 >= ind2.obj2:
                if ind1.obj1 < ind2.obj1:
                    efficient = False
                    break
        if not efficient:
            is_efficient[i] = efficient
    selected_individuals = set([i for i, v in enumerate(is_efficient) if v])
    if ndSolSelection:
        return [cp[i] for i in selected_individuals]
    if len(selected_individuals) < N_p:
        while len(selected_individuals) != N_p:
            i = random.choice(list(set(list(range(len(cp)))).difference(selected_individuals)))
            selected_individuals.add(i)
    elif len(selected_individuals) > N_p:
        selected_individuals = random.sample(selected_individuals, N_p)
    #
    return [cp[i] for i in selected_individuals]


def localSearch(prevPopulation):
    newPopulation = []
    for ind0 in prevPopulation:
        ind1 = neighborhoodSearch(ind0)
        while ind1 is not None:
            ind0 = ind1
            ind1 = neighborhoodSearch(ind0)
        newPopulation.append(ind0)
    return newPopulation


def neighborhoodSearch(ind0):
    chromosomeLen = len(ind0.g1) + len(ind0.g2)
    for i in range(chromosomeLen):
        if i < len(ind0.g1):
            cur_l = ind0.g1[i]
            for l in ind0.inputs['L']:
                if cur_l == l:
                    continue
                ind1 = ind0.clone()
                ind1.g1[i] = l
                ind1.evaluation()
                if ind0.obj1 < ind1.obj1 and ind0.obj2 > ind1.obj2:
                    return ind1
        else:
            j = i - len(ind0.g1)
            cur_m = ind0.g2[j]
            for m in range(2):
                if cur_m == m:
                    continue
                ind1 = ind0.clone()
                ind1.g2[j] = m
                ind1.evaluation()
                if ind0.obj1 < ind1.obj1 and ind0.obj2 > ind1.obj2:
                    return ind1
    else:
        return None


def run(inputs):
    if 'N_g' not in inputs:
        N_g, N_p, N_o, p_c, p_m = 200, 50, 40, 0.5, 0.5
    else:
        N_g, N_p, N_o, p_c, p_m = [inputs.get(k) for k in ['N_g', 'N_p', 'N_o', 'p_c', 'p_m']]
    #
    population = genPopulation(inputs, N_p)
    evolution = []
    for gn in range(N_g):
        population = localSearch(population)
        #
        obj1_values, obj2_values = [], []
        for ind in population:
            obj1_values.append(ind.obj1)
            obj2_values.append(ind.obj2)
        offspring = random.sample([ind.clone() for ind in population], N_o)
        #
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < p_c:
                cxInd(ind1, ind2)
        #
        for ind in offspring:
            if random.random() < p_m:
                mutInd(ind)
        #
        for ind in offspring:
            ind.evaluation()
        population = selInds(population, offspring, N_p)
        #
        objs = set()
        for ind in selInds(population, [], N_p, ndSolSelection=True):
            k = (ind.obj1, ind.obj2)
            objs.add(k)
        evolution.append(objs)
    #
    paretoFront = {}
    for ind in selInds(population, [], N_p, ndSolSelection=True):
        k = (ind.obj1, ind.obj2)
        if k in paretoFront:
            ind0 = paretoFront[k]
            if sum(ind.g1) < sum(ind0.g1):
                paretoFront[k] = ind
        else:
            paretoFront[k] = ind
    #
    return paretoFront, evolution


def test():
    from problems import p0, p_Lv4_Mon_H9
    inputs = p0()
    # inputs = p_Lv4_Mon_H9()
    run(inputs)


if __name__ == '__main__':
    test()