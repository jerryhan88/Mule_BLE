from problems import *


def run(inputs, ms):
    b_pl = []
    for b in inputs['B']:
        for l in inputs['L']:
            is_feasible = True
            for k in inputs['K']:
                xProb = 1
                for m in ms:
                    xProb *= (1 - inputs['p_kmbl'][k, m, b, l])
                if 1 - xProb < inputs['R']:
                    is_feasible = False
                    break
            if is_feasible:
                b_pl.append(l)
                break
        else:
            b_pl.append(None)
    if None in b_pl:
        obj1 = MIN_OBJ1
    else:
        obj1 = min([inputs['c_b'][b] - inputs['e_l'][b_pl[b]] for b in inputs['B']])
    obj2 = len(ms)
    return obj1, obj2


def test():
    inputs = p0()
    # inputs = p_Lv4_Mon_H9()
    mo = order_mules(inputs)

    print(run(inputs, mo[:4]))


if __name__ == '__main__':
    test()