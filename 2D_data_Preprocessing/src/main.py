import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
import traceback
import multiprocessing as mp
import logging


def excepthook(excType, excValue, tracebackobj):
    traceback.print_tb(tracebackobj, None, None)
    print(excType, excValue)


sys.excepthook = excepthook

if __name__ == '__main__':
    logging.basicConfig(format='[line:%(lineno)d] %(filename)s %(asctime)s %(levelname)s %(message)s', level=logging.NOTSET)
    mp.set_start_method('spawn', force=True)
    app = QApplication(sys.argv)
    mainwindow = MainWindow.MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
