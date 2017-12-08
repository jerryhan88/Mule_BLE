from _prevWorks.data_processing import *

def ex1():
    numCols, numRows = 5, 5
    numTimeSlots = 2
    muleTraj = [  # X continuous trajectory
        [
            {(0, 2): 0.3, (2, 2): 0.3, (4, 3): 0.4},
            {(1, 2): 0.2, (3, 2): 0.1, (3, 4): 0.4}
        ],
        [
            {(4, 2): 0.5, (2, 2): 0.2, (4, 4): 0.1},
            {(2, 2): 0.1, (3, 4): 0.5, (0, 2): 0.4}
        ]
    ]
    I = 500
    powerLv, consumedE = [1, 2, 3, I], [5, 10, 15, I]
    beaconPos, remainingBC = [(0, 0), (2, 1), (4, 2)], [400, 300, 300]
    minPowLv = [
        [[1, 1, 2, 3, I],
         [1, 2, 3, I, I],
         [2, 3, I, I, I],
         [3, I, I, I, I],
         [I, I, I, I, I]],

        [[3, 2, 1, 2, 3],
         [2, 1, 1, 1, 2],
         [3, 2, 1, 2, 3],
         [I, 3, 2, 3, I],
         [I, I, 3, I, I]],

        [[I, I, I, 3, 2],
         [I, I, 3, 2, 1],
         [I, 3, 2, 1, 1],
         [I, I, 3, 2, 1],
         [I, I, I, 3, 2]],
    ]

    inputs = [numCols, numRows,
                numTimeSlots,
                muleTraj,
                powerLv, consumedE,
                beaconPos, remainingBC,
                minPowLv]
    check_feasiblity(inputs)
    #
    return numCols, numRows, \
           numTimeSlots, \
           muleTraj, \
           powerLv, consumedE, \
           beaconPos, remainingBC, \
           minPowLv



def realProblem_Lv4():
    #
    fpath = 'realProb.pkl'
    if not opath.exists(fpath):
        zones2landmarks, landmarks2zones = get_zoneNlandmarkInfo()
        beacons2landmarks = get_beaconInfo()
        muleTraj2landmarks = get_trajDist()
        _objects = [zones2landmarks, landmarks2zones, beacons2landmarks, muleTraj2landmarks]
        with open(fpath, 'wb') as fp:
            pickle.dump(_objects, fp)
    else:
        _objects = None
        with open(fpath, 'rb') as fp:
            _objects = pickle.load(fp)
        zones2landmarks, landmarks2zones, beacons2landmarks, muleTraj2landmarks = _objects
    #
    numCols, numRows = -1e400, -1e400
    for zi, zj in zones2landmarks:
        if numRows < zi:
            numRows = zi
        if numCols < zj:
            numCols = zj
    numTimeSlots = 4
    muleTraj = []
    for indi_mulTraj0 in muleTraj2landmarks:
        indi_muleTraj = []
        for ts_Traj in indi_mulTraj0:
            zone_prob = {}
            for locID, prob in ts_Traj.items():
                zone_prob[landmarks2zones[str(locID)]] = prob
            indi_muleTraj.append(zone_prob)
        muleTraj.append(indi_muleTraj)

    I = 500
    powerLv, consumedE = [1, 2, 3, I], [5, 10, 15, I]
    beaconPos, remainingBC = [], []
    for locID in beacons2landmarks.values():
        beaconPos.append(landmarks2zones[str(locID)])
        remainingBC.append(300)
    minPowLv = []
    for bi, bj in beaconPos:
        bePow = [[I for _ in range(numCols)] for _ in range(numRows)]
        for zi in range(numCols):
            for zj in range(numRows):
                manDist = abs(bi - zi) + abs(bj - zj)
                if manDist > 3:
                    bePow[zj][zi] = I
                else:
                    bePow[zj][zi] = manDist
        minPowLv.append(bePow)
    inputs = [numCols, numRows,
              numTimeSlots,
              muleTraj,
              powerLv, consumedE,
              beaconPos, remainingBC,
              minPowLv]
    check_feasiblity(inputs)
    #
    return numCols, numRows, \
           numTimeSlots, \
           muleTraj, \
           powerLv, consumedE, \
           beaconPos, remainingBC, \
           minPowLv

def check_feasiblity(inputs):
    numCols, numRows, \
    bK, \
    muleTraj, \
    powerLv, consumedE, \
    beaconPos, remainingBC, \
    minPowLv = inputs
    #
    # Check mules' trajectory for each time slot
    #    Mule's position (location) should be within a grid
    #    The sum of probability at a time slot should be (less than or) equal to 1
    for mule in muleTraj:
        timeSlotCounter = 0
        for timeSlot in mule:
            sumProb = 0
            for pos, prob in timeSlot.items():
                sumProb += prob
                zi, zj = pos
                assert zi < numCols
                assert zj < numRows
            assert sumProb <= 1 + 0.01, sumProb
            timeSlotCounter += 1
        assert timeSlotCounter == bK
    #
    # Check positive correlation between power level and energy consumption
    #
    for i in range(len(powerLv) - 1):
        assert powerLv[i] < powerLv[i + 1]
        assert consumedE[i] < consumedE[i + 1]
    #
    # Check beaconPos' position and remaining battery capacity
    #
    for i in range(len(beaconPos)):
        bi, bj = beaconPos[i]
        assert bi < numCols
        assert bj < numRows
        assert 0 < remainingBC[i]


def convert_notations4mm(inputs):
    #
    # Convert notations for the mathematical model
    #
    numCols, numRows, \
    numTimeSlots, \
    muleTraj, \
    powerLv, consumedE, \
    beaconPos, remainingBC, \
    minPowLv = inputs
    #
    Z = [(i, j) for i in range(numCols) for j in range(numRows)]
    M = list(range(len(muleTraj)))
    bK = numTimeSlots
    K = list(range(bK))
    p_mkz = {}
    for mm in M:
        for k in K:
            for z in Z:
                if z in muleTraj[mm][k]:
                    p_mkz[mm, k, z] = muleTraj[mm][k][z]
                else:
                    p_mkz[mm, k, z] = 0
    Z_F = []
    for z in Z:
        if z == (4, 2):
            print()
        for k in K:
            sumProb = 0
            for mm in M:
                sumProb += p_mkz[mm, k, z]
            if sumProb == 0:
                break
        else:
            Z_F.append(z)
    #
    B = list(range(len(beaconPos)))
    c_b = remainingBC[:]
    L = powerLv[:]
    e_l = {L[i]: consumedE[i] for i in range(len(L))}
    n_bz = {}
    for b in B:
        for z in Z:
            zi, zj = z
            n_bz[b, z] = minPowLv[b][zj][zi]
    #
    return Z, M, bK, K, p_mkz, Z_F, B, c_b, L, e_l, n_bz


if __name__ == '__main__':
    realProblem_Lv4()