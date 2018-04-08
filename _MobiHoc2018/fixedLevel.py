from problems import *


def run(inputs):
    l = inputs['FL']
    mo = order_mules(inputs)
    for i in range(len(mo)):
        ms = mo[:i + 1]
        is_feasible = True
        for b in inputs['B']:
            for k in inputs['K']:
                xProb = 1
                for m in ms:
                    xProb *= (1 - inputs['p_kmbl'][k, m, b, l])
                if 1 - xProb < inputs['R']:
                    is_feasible = False
                    break
        if is_feasible:
            break
    else:
        is_feasible = False
    obj1 = min([inputs['c_b'][b] - inputs['e_l'][l] for b in inputs['B']])
    obj2 = len(ms) if is_feasible else len(inputs['M'])
    ls = [l for _ in inputs['B']]
    return obj1, obj2, ls, ms


def test():
    from problems import p0, p_Lv4_Mon_H9
    inputs = p0()
    # inputs = p_Lv4_Mon_H9()
    print(run(inputs, inputs['L'][-2]))


if __name__ == '__main__':
    test()