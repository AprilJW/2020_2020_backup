import sys
import traceback
import logging

from PyQt5.QtWidgets import QApplication

from ui.MainWindow import MainWindow

def excepthook(excType, excValue, tracebackobj):
    traceback.print_tb(tracebackobj, None, None)
    print(excType, excValue)
    
sys.excepthook = excepthook

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s %(message)s")
    logging.disable(logging.NOTSET - 10)  # Enable NOTSET
    
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
