from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint
import shapely
import sys


colors = [QColor(255, 0, 0),
          QColor(50, 55, 100),
          QColor(0, 0, 255),
          QColor(171, 121, 66),
          QColor(148, 32, 146)]


canvasSize = (800, 800)
beaconPos = [(200, 200), (300, 400), (650, 580)]
beaconRad = 10
tranRange = [50, 100, 200]
tr = tranRange[1]

muleTrajectory = {
    0: [
        [(517, 115), (774, 326), (603, 600), (403, 700)],
        [(400, 100), (100, 372), (453, 657)],
        [(300, 51), (68, 150), (240, 460), (500, 700)]
       ],

    # 1: [
    #     [(750, 121), (100, 662)],
    #     [(700, 121), (380, 362), (100, 620)],
    #     [(780, 150), (460, 500), (150, 702)],
    #     ],
    #
    # 2: [
    #     [(190, 155), (239, 403), (389, 663), (704, 667)],
    #     [(170, 125), (200, 433), (349, 763)],
    #    ],
    #
    # 3: [
    #     [(76, 703), (416, 497), (756, 448)],
    #     [(70, 653), (786, 548)],
    #    ],
    #
    # 4: [
    #     [(170, 486), (530, 371), (661, 11)],
    #     [(680, 11), (701, 701), ],
    #    ]
    }

from shapely.geometry import LineString, Point


for mid, trajectories in muleTrajectory.items():
    for tid, aTrajectory in enumerate(trajectories):
        for bid, (px, py) in enumerate(beaconPos):
            covAra = Point(px, py).buffer(tr)
            print('mid: %d, tid: %d, bid: %d' % (mid, tid, bid), covAra.intersects(LineString(aTrajectory)))

    print('')



class Beacon(object):
    def __init__(self, bid, px, py):
        self.bid = bid
        self.px, self.py = px, py
        self.centerPos = QPoint(self.px, self.py)

    def draw(self, qp):
        qp.setPen(QPen(Qt.black, 0.5))
        qp.setBrush(Qt.NoBrush)
        qp.drawEllipse(self.centerPos, tr, tr)

        qp.setPen(QPen(Qt.black, 1))
        qp.setBrush(QColor(0, 200, 0))
        qp.drawEllipse(self.centerPos, beaconRad, beaconRad)

        qp.setFont(QFont('Decorative', 20))
        qp.drawText(self.px, self.py, 20, 20, Qt.AlignCenter, 'b%d' % self.bid)




class Mule(object):
    def __init__(self, mid, trajectories):
        self.mid, self.trajectories = mid, trajectories

    def draw(self, qp):
        qp.setFont(QFont('Decorative', 15))
        qp.setPen(colors[self.mid])

        for tid, aTrajectory in enumerate(self.trajectories):
            for i in range(1, len(aTrajectory)):
                x0, y0 = aTrajectory[i - 1]
                x1, y1 = aTrajectory[i]
                qp.drawLine(x0, y0, x1, y1)
            px, py = aTrajectory[0]
            qp.drawText(px, py-15, 60, 15, Qt.AlignCenter, 'm%d(t%d)' % (self.mid, tid))

beacons = [Beacon(bid, px, py) for bid, (px, py) in enumerate(beaconPos)]
mules = [Mule(mid, trajectories) for mid, trajectories in muleTrajectory.items()]




class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        w,h = canvasSize
        self.setGeometry(100, 150, w,h)
        self.setWindowTitle('Viz')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawCanvas(qp)
        qp.end()

    def drawCanvas(self, qp):
        for m in mules:
            m.draw(qp)

        for b in beacons:
            b.draw(qp)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    # ex = Example(realProblem_Lv4())
    sys.exit(app.exec_())