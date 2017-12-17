import random


random.seed(64)
NUM_POPULATION = 20
MIN_OBJ1 = -100000
MAX_OBJ2 = 100000
NGEN = 100


class Individual(object):
    def __init__(self, inputs):
        self.inputs = inputs
        #
        self.g1, self.g2 = [], []
        self.obj1, self.obj2 = MIN_OBJ1, MAX_OBJ2

    def __repr__(self):
        return '|%s|%s' % (''.join(['%d' % v for v in self.g1]), ''.join(['%d' % v for v in self.g2]))

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
        if is_feasible:
            self.obj1 = min_rb
            self.obj2 = sum(self.g2)

    def clone(self):
        c = Individual(self.inputs)
        c.g1 = self.g1[:]
        c.g2 = self.g2[:]
        return c

def genPopulation(inputs):
    population = []
    for _ in range(NUM_POPULATION):
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


def selInds(prevGen, newGen):
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
    print('\t', 'nd', [(cp[i], cp[i].obj1, cp[i].obj2) for i in selected_individuals if cp[i].obj1 > MIN_OBJ1 and cp[i].obj2 < MAX_OBJ2])
    if len(selected_individuals) < NUM_POPULATION:
        while len(selected_individuals) != NUM_POPULATION:
            i = random.choice(list(set(list(range(len(cp)))).difference(selected_individuals)))
            selected_individuals.add(i)
    elif len(selected_individuals) > NUM_POPULATION:
        selected_individuals = random.sample(selected_individuals, NUM_POPULATION)
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
    population = genPopulation(inputs)
    CXPB = 0.5
    MUTPB = 0.5
    NOFF = int(NUM_POPULATION * 0.8)
    for gn in range(NGEN):
        print('GN', gn)
        #
        population = localSearch(population)
        #
        obj1_values, obj2_values = [], []
        for ind in population:
            obj1_values.append(ind.obj1)
            obj2_values.append(ind.obj2)
        print('\t', [(ind, ind.obj1, ind.obj2) for ind in population if ind.obj1 > MIN_OBJ1 and ind.obj2 < MAX_OBJ2])

        offspring = random.sample([ind.clone() for ind in population], NOFF)
        #
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                cxInd(ind1, ind2)
        #
        for ind in offspring:
            if random.random() < MUTPB:
                mutInd(ind)
        #
        for ind in offspring:
            ind.evaluation()
        population = selInds(population, offspring)
    print('LAST')


def test():
    from problems import p0, p_Lv4_Mon_H9
    inputs = p0()
    # inputs = p_Lv4_Mon_H9()
    run(inputs)


if __name__ == '__main__':
    test()