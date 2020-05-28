import sys
from PyQt5.QtWidgets import QApplication
from ui.MainWindow import MainWindow
import traceback

def excepthook(excType, excValue, tracebackobj):
    traceback.print_tb(tracebackobj, None, None)
    print(excType, excValue)
    
sys.excepthook = excepthook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())