############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.pyplot import figure
#import matplotlib.pyplot as plt

class figureCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        self.fig = figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        #self.fig, self.axes = plt.subplots()
        self.draw_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def draw_figure(self):
        pass


class MyStaticMplCanvas(figureCanvas):
    """Simple canvas with a sine plot."""

    def draw_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)

'''
    def draw_figure(self):
        x = arange(4)
        money = [1.5e5, 2.5e6, 5.5e6, 2.0e7]
        self.axes.bar(x, money, tick_label=['Bill', 'Fred', 'Mary', 'Sue'])
        #plt.bar(x, money)
        #plt.xticks(x, ('Bill', 'Fred', 'Mary', 'Sue'))
'''

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        l.addWidget(sc)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


if __name__ == '__main__':

    qApp = QtWidgets.QApplication(sys.argv)

    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())