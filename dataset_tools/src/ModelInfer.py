from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
from Image_comparer import InfererMaskRCNN, InfererFCNKeras, InfererRetinaNet


class MainWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget(self)
        mrcnn_infer_page = InfererMaskRCNN.Inferer()
        fcn_keras_page = InfererFCNKeras.Inferer()
        retinanet_page = InfererRetinaNet.Inferer()
        self.tabs.addTab(mrcnn_infer_page, "maskrcnn infer")
        self.tabs.addTab(fcn_keras_page, "fcn infer")
        self.tabs.addTab(retinanet_page, "retinanet infer")
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.setWindowTitle("model inferer")
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwizard = MainWizard()
    mainwizard.show()
    sys.exit(app.exec())