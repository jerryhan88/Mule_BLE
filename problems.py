from shapely.geometry import LineString, Point


def p0():
    canvasSize = (800, 800)
    beaconPos = [(200, 200), (300, 400), (650, 580)]
    beaconRad = 10
    tranRange = [50, 100, 200]
    ts_muleTrajectory = [{
        0: [
            (1, [(517, 115), (774, 326), (603, 600), (403, 700)]),
            (1, [(400, 100), (100, 372), (453, 657)]),
            (1, [(300, 51), (68, 150), (240, 460), (500, 700)]),
            (1, []),
        ],

        1: [
            (2, [(750, 121), (100, 662)]),
            (3, [(700, 121), (380, 362), (100, 620)]),
            (3, [(780, 150), (460, 500), (150, 702)]),
            (1, []),
        ],

        2: [
            (1, [(190, 155), (239, 403), (389, 663), (704, 667)]),
            (3, [(170, 125), (200, 433), (349, 763)]),
        ],

        3: [
            (2, [(76, 703), (416, 497), (756, 448)]),
            (3, [(70, 653), (786, 548)]),
            (1, []),
        ],

        4: [
            (4, [(170, 486), (530, 371), (661, 11)]),
            (2, [(680, 11), (701, 701)]),
        ]
    }]
    bK = len(ts_muleTrajectory)
    K = list(range(bK))
    mules = set()
    for muleTrajectory in ts_muleTrajectory:
        for mid in muleTrajectory.keys():
            mules.add(mid)
    M = list(range(len(mules)))
    B = list(range(len(beaconPos)))
    c_b = [500, 300, 400]
    L = list(range(len(tranRange)))
    e_l = [20, 50, 100]
    p_kmbl = {}
    for k, muleTrajectory in enumerate(ts_muleTrajectory):
        for m, trajectories in muleTrajectory.items():
            weightSum = sum(w for w, _ in trajectories)
            for tid, (w, aTrajectory) in enumerate(trajectories):
                if not aTrajectory:
                    continue
                for b, (px, py) in enumerate(beaconPos):
                    for l in L:
                        covAra = Point(px, py).buffer(tranRange[l])
                        tra = LineString(aTrajectory)
                        if covAra.intersects(tra):
                            if not (k, m, b, l) in p_kmbl:
                                p_kmbl[k, m, b, l] = 0
                            p_kmbl[k, m, b, l] += w / weightSum
                        else:
                            if not (k, m, b, l) in p_kmbl:
                                p_kmbl[k, m, b, l] = 0

    R = 0.9

    return {'K': K, 'M': M, 'B': B,
            'c_b': c_b, 'L': L, 'e_l': e_l,
            'p_kmbl': p_kmbl, 'R': R}


if __name__ == '__main__':
    p0()