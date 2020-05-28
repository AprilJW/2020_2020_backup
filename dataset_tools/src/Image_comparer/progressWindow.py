############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QBasicTimer
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QGroupBox,
                             QHBoxLayout, QSplitter, QSizePolicy, QGridLayout,
                             QLabel, QProgressBar, QPushButton)

class progressWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.initUI()

    def initUI(self):

        # create layout
        self.progress_groupbox = QGroupBox('Progress')
        self.body_grid_layout = QGridLayout()
        self.body_vbox = QVBoxLayout()

        # set up layout
        self.body_vbox.addLayout(self.body_grid_layout)
        self.progress_groupbox.setLayout(self.body_vbox)

        self.window_vbox = QVBoxLayout()
        self.window_vbox.addWidget(self.progress_groupbox)
        self.setLayout(self.window_vbox)

        self._number_of_progresses = 0
        self.progress_bars = []

    def getNumberOfProgress(self):

        return self._number_of_progresses

    def setNumberOfProgress(self, number_of_progresses):

        self._number_of_progresses = number_of_progresses

    def addProgress(self, model_name, initial_value = 0):

        label = QLabel(model_name)
        progressbar = QProgressBar()

        current_number_of_progresses = self.getNumberOfProgress()

        self.body_grid_layout.addWidget(label, current_number_of_progresses, 0, 1, 1)
        self.body_grid_layout.addWidget(progressbar, current_number_of_progresses, 1, 1, 5)

        progressbar.setValue(initial_value)

        self.progress_bars.append(progressbar)

        self.setNumberOfProgress(current_number_of_progresses + 1)


    def addMultipleProgress(self, number_of_progress):

        for which_progress in range(number_of_progress):
            self.addProgress('Model {0}'.format(which_progress + 1))

if __name__ == '__main__':

    app = QApplication(sys.argv)
    progress_window = progressWindow()
    #analyse_window.setLayout(analyse_window.analyse_window_body_vbox)
    progress_window.addMultipleProgress(2)
    progress_window.show()
    sys.exit(app.exec_())