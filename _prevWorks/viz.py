import sys

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QApplication
from problems import *

from _prevWorks.matheModel import run as run_mm


class zone(object):
    def __init__(self, zid, zi, zj):
        self.zid, self.zi, self.zj = zid, zi, zj
        self.feasible, self.covered = False, False

    def initDrawing(self, xUnit, yUnit):
        self.x_lu, self.y_lu = self.zi * xUnit, self.zj * yUnit
        self.x_ru, self.y_ru = self.x_lu + xUnit, self.y_lu
        self.x_rb, self.y_rb = self.x_ru, self.y_ru + yUnit
        self.x_lb, self.y_lb = self.x_rb - xUnit, self.y_rb
        self.w, self.h = xUnit, yUnit

    def draw(self, qp):
        if self.feasible:
            qp.setPen(QPen(Qt.black, 1))
            qp.setBrush(QColor(200, 0, 0))
            qp.drawRect(self.x_lu, self.y_lu, self.w, self.h)
        if self.covered:
            qp.setPen(QPen(Qt.black, 1))
            qp.setBrush(QColor(100, 100, 100, 50))
            qp.drawRect(self.x_lu, self.y_lu, self.w, self.h)


class beacon(object):
    def __init__(self, bid, bi, bj):
        self.bid, self.bi, self.bj = bid, bi, bj

    def initDrawing(self, xUnit, yUnit):
        self.centerPos = QPoint((self.bi + 0.5) * xUnit, (self.bj + 0.5) * yUnit)
        self.r = min(xUnit, yUnit) / 7

    def draw(self, qp):
        qp.setPen(QPen(Qt.black, 1))
        qp.setBrush(QColor(0, 200, 0))
        qp.drawEllipse(self.centerPos, self.r, self.r)


class Example(QWidget):
    def __init__(self, inputs):
        super().__init__()
        #
        numCols, numRows, \
        numTimeSlots, \
        muleTraj, \
        powerLv, consumedE, \
        beaconPos, remainingBC, \
        minPowLv = inputs
        bestSol = run_mm(inputs)
        #

        Z, M, bK, K, p_mkz, Z_F, B, c_b, L, e_l, n_bz = convert_notations4mm(inputs)

        print(muleTraj)

        self.numCols, self.numRows = numCols, numRows
        self.Z = {(zi, zj): zone('%d#%d' % (zi, zj), zi, zj)
                  for zi in range(self.numCols) for zj in range(self.numRows)}
        for zi, zj in Z_F:
            self.Z[zi, zj].feasible = True
        self.B = {bid: beacon(bid, bi, bj) for bid, (bi, bj) in enumerate(beaconPos)}

        bpl = [0 for _ in range(len(bestSol))]
        for bid, pl in bestSol:
            bpl[bid] = pl
        for bid in range(len(minPowLv)):
            for zj in range(len(minPowLv[bid])):
                for zi in range(len(minPowLv[bid][zj])):
                    if minPowLv[bid][zj][zi] <= bpl[bid]:
                        self.Z[zi, zj].covered = True
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 150, 800, 800)
        size = self.size()
        self.w, self.h = size.width(), size.height()
        self.xUnit, self.yUnit = self.w / self.numCols, self.h / self.numRows
        for z in self.Z.values():
            z.initDrawing(self.xUnit, self.yUnit)
        for b in self.B.values():
            b.initDrawing(self.xUnit, self.yUnit)
        self.setWindowTitle('Viz')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawLines(qp)
        qp.end()

    def drawLines(self, qp):
        for z in self.Z.values():
            z.draw(qp)
        for b in self.B.values():
            b.draw(qp)

        qp.setBrush(QColor(0, 0, 0))
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        qp.setPen(pen)
        for i in range(self.numRows):
            x = self.xUnit * (i + 1)
            qp.drawLine(x, 0, x, self.h)
        for i in range(self.numCols):
            y = self.yUnit * (i + 1)
            qp.drawLine(0, y, self.w, y)


def run_realProblem():
    app = QApplication(sys.argv)
    ex = Example(ex1())
    sys.exit(app.exec_())
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example(ex1())
    # ex = Example(realProblem_Lv4())
    sys.exit(app.exec_())