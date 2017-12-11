import sys
#
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import QWidget, QApplication
#
from dataProcessing import *
#
windowX, windowY = 100, 150
windowW, windowH = 1000, 1000
floor = 'Lv4'

# nCOLs, nROWs, zones = get_gridLayout(floor)


class Zone(object):
    def __init__(self, zi, zj):
        self.zi, self.zj = zi, zj
        self.belonged_axis, self.axisID = False, None
        self.lmID = None

    def initDrawing(self, xUnit, yUnit):
        self.x_lu, self.y_lu = self.zi * xUnit, self.zj * yUnit
        self.x_ru, self.y_ru = self.x_lu + xUnit, self.y_lu
        self.x_rb, self.y_rb = self.x_ru, self.y_ru + yUnit
        self.x_lb, self.y_lb = self.x_rb - xUnit, self.y_rb
        self.w, self.h = xUnit, yUnit

    def draw(self, qp):
        if self.belonged_axis:
            qp.setFont(QFont('Decorative', 10))
            qp.drawText(self.x_lu, self.y_lu, self.w, self.h, Qt.AlignCenter, self.axisID)
        if self.lmID:
            qp.setFont(QFont('Decorative', 15))
            qp.drawText(self.x_lu, self.y_lu, self.w, self.h, Qt.AlignHCenter, self.lmID)


class Beacon(object):
    def __init__(self, bid, z):
        self.bid, self.z = bid, z
        self.plCovZ = {}

    def initDrawing(self, xUnit, yUnit):
        self.cx, self.cy = (self.z.x_lu + self.z.x_rb) / 2, (self.z.y_lu + self.z.y_rb) / 2
        self.centerPos = QPoint(self.cx, self.cy)
        self.r = min(xUnit, yUnit) / 8

    def draw(self, qp):
        if self.bid == '104020201':
            qp.setPen(QPen(Qt.black, 1))
            qp.setBrush(QColor(200, 0, 0))
            for z in self.plCovZ[0]:
                cx, cy = (z.x_lu + z.x_rb) / 2, (z.y_lu + z.y_rb) / 2
                qp.drawRect(cx, cy, z.w / 2, z.h / 2)
        #
        qp.setPen(QPen(Qt.black, 1))
        qp.setBrush(QColor(0, 200, 0))
        qp.drawEllipse(self.centerPos, self.r, self.r)


class Mule(object):
    def __init__(self, mid):
        self.mid = mid






class LayoutW(QWidget):
    def __init__(self):
        super().__init__()
        self.numCols, self.numRows, grid_lmID = get_gridLayout(floor)
        self.zones, self.lmID2zone = {}, {}
        for zi in range(self.numCols):
            for zj in range(self.numRows):
                z = Zone(zi, zj)
                if zi == 0 and zj == 0:
                    z.belonged_axis, z.axisID = True, '-'
                elif zi == 0:
                    z.belonged_axis, z.axisID = True, str(zj)
                elif zj == 0:
                    z.belonged_axis, z.axisID = True, str(zi)
                else:
                    if (zi, zj) in grid_lmID:
                        _lmID = grid_lmID[zi, zj]
                        if type(_lmID) == list:
                            z.lmID = ', '.join(_lmID)
                            for lmID in _lmID:
                                self.lmID2zone[lmID] = z
                        else:
                            z.lmID = _lmID
                            self.lmID2zone[_lmID] = z
                self.zones[zi, zj] = z
        #
        self.beacons = {}
        beacon2landmark, landmark2beacon = get_beaconInfo(floor)
        plCovLD = get_plCovLD(floor)
        for beaconID in beacon2landmark:
            z = self.lmID2zone[beacon2landmark[beaconID]]
            b = Beacon(beaconID, z)
            for l in range(len(PL_RANGE)):
                b.plCovZ[l] = [self.lmID2zone[lmID] for lmID in plCovLD[beaconID, l]]
            self.beacons[beaconID] = b


        self.initUI()

    def initUI(self):
        self.setGeometry(windowX, windowY, windowW, windowH)
        size = self.size()
        self.w, self.h = size.width(), size.height()
        self.xUnit, self.yUnit = self.w / self.numCols, self.h / self.numRows
        for z in self.zones.values():
            z.initDrawing(self.xUnit, self.yUnit)
        for b in self.beacons.values():
            b.initDrawing(self.xUnit, self.yUnit)
        self.setWindowTitle('LayoutViz')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawLayout(qp)
        qp.end()

    def drawLayout(self, qp):
        for z in self.zones.values():
            z.draw(qp)
        for b in self.beacons.values():
            b.draw(qp)
        #
        for i in range(self.numRows):
            x = self.xUnit * (i + 1)
            qp.drawLine(x, 0, x, self.h)
        for j in range(self.numCols):
            y = self.yUnit * (j + 1)
            qp.drawLine(0, y, self.w, y)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LayoutW()
    sys.exit(app.exec_())