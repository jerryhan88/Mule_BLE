from gurobipy import *

from _prevWorks.problems import *

#

EPSILON = 0.01


def run(inputs):
    Z, M, bK, K, p_mkz, Z_F, B, c_b, L, e_l, n_bz = convert_notations4mm(inputs)
    #
    # Define decision variables
    #
    mm = Model('')
    x_z, x_bz, a_b, a_bl, y_m = {}, {}, {}, {}, {}
    R = mm.addVar(vtype=GRB.CONTINUOUS, name='R')
    for z in Z_F:
        zi, zj = z
        x_z[z] = mm.addVar(vtype=GRB.BINARY, name='xz[%d,%d]' % (zi, zj))
        for b in B:
            x_bz[b, z] = mm.addVar(vtype=GRB.BINARY, name='xbz[%d,%d,%d]' % (b, zi, zj))
    for b in B:
        for l in L:
            a_bl[b, l] = mm.addVar(vtype=GRB.BINARY, name='abl[%d,%d]' % (b, l))
    for m in M:
        y_m[m] = mm.addVar(vtype=GRB.BINARY, name='ym[%d]' % m)
    mm.update()
    #
    # Define objectives
    #   Set number of objectives
    NUM_OBJS = 4
    mm.ModelSense = GRB.MAXIMIZE
    mm.NumObj = NUM_OBJS
    #
    # The first objective
    #   eq:maxMinEC_linV
    mm.setParam(GRB.Param.ObjNumber, 0)
    mm.ObjNPriority = 4
    mm.setAttr(GRB.Attr.ObjN, [R], [1])
    #
    # The second objective
    #   eq:minDCZ
    mm.setParam(GRB.Param.ObjNumber, 1)
    mm.ObjNPriority = 3
    dvs, coefs = [], []
    for z in Z_F:
        dvs.append(x_z[z])
        coefs.append(-1)
    mm.setAttr(GRB.Attr.ObjN, dvs, coefs)
    #
    # The third objective
    #   eq:minM
    mm.setParam(GRB.Param.ObjNumber, 2)
    mm.ObjNPriority = 2
    dvs, coefs = [], []
    for m in M:
        dvs.append(y_m[m])
        coefs.append(-1)
    mm.setAttr(GRB.Attr.ObjN, dvs, coefs)
    #
    # The forth objective
    #   eq:maxP
    mm.setParam(GRB.Param.ObjNumber, 3)
    mm.ObjNPriority = 1
    dvs, coefs = [], []
    for z in Z_F:
        sumPopularity = 0
        for m in M:
            for k in K:
                sumPopularity += p_mkz[m, k, z]
        dvs.append(x_z[z])
        coefs.append(sumPopularity)
    mm.setAttr(GRB.Attr.ObjN, dvs, coefs)
    #
    # Define constrains
    #
    for b in B:
        mm.addConstr(quicksum(x_bz[b, z] for z in Z_F) == 1,
                     name='cp[%d]' % b)  # eq:collectionPoint
        mm.addConstr(quicksum(a_bl[b, l] for l in L) == 1,
                     name='pls[%d]' % b)  # eq:powLvSelection
        mm.addConstr(quicksum(n_bz[b, z] * x_bz[b, z] for z in Z_F) <= quicksum(l * a_bl[b, l] for l in L),
                     name='mpl[%d]' % b)  # eq:minPowLv
        mm.addConstr(R <= c_b[b] - quicksum(e_l[l] * a_bl[b, l] for l in L),
                     name='ebc[%d]' % b)  # eq:expectedBC
    for z in Z_F:
        zi, zj = z
        mm.addConstr(quicksum(x_bz[b, z] for b in B) * EPSILON <= x_z[z],
                     name='dcz[%d,%d]' % (zi, zj))  # eq:dataColZone
    for m in M:
        mm.addConstr(quicksum(p_mkz[m,k,z] * x_z[z] for z in Z_F for k in K) * EPSILON <= y_m[m],
                     name='pm[%d]' % m)  # eq:passingMule

    mm.write('matheModel.lp')
    mm.optimize()


    nSolutions = mm.SolCount
    bestSol = []
    for e in range(nSolutions):
        mm.setParam(GRB.Param.SolutionNumber, e)
        for b in B:
            for l in L:
                if a_bl[b, l].Xn > 0.5:
                    print('\t\t', b, l, a_bl[b, l].Xn)
                    if e == 0:
                        bestSol.append((b, l))
        for i in range(NUM_OBJS):
            mm.setParam(GRB.Param.ObjNumber, i)
            print('\t Obj%d' % i, end='')
            print(' %6g\n' % mm.ObjNVal, end='')
        print('')
    #
    return bestSol


if __name__ == '__main__':
    run(ex1())