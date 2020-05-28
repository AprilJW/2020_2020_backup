############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QGroupBox,
                             QHBoxLayout, QSplitter, QSizePolicy)

class analyseWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.initUI()

    def initUI(self):

        # create hbox for stat_groupbox
        self.stats_hbox = QHBoxLayout()

        # set up stats groupboxes
        self.stats_groupbox = QGroupBox('Statistics')
        self.stats_groupbox.setLayout(self.stats_hbox)

        # set up scrollArea for the compare widget
        #self.compare_frame = QFrame()
        #self.analyse_window_scroll_area = QScrollArea()
        #self.analyse_window_scroll_area.setWidget(self.compare_frame)
        #self.compare_frame.setFrameStyle(QFrame.WinPanel | QFrame.Raised)
        #self.compare_frame.setLineWidth(3)
        #self.analyse_window_scroll_area.setWidgetResizable(True)

        # set up comapre vbox
        self.compare_vbox = QVBoxLayout()
        #self.compare_vbox.addWidget(self.analyse_window_scroll_area)

        # set up compare groupbox
        self.compare_groupbox = QGroupBox('Compare Results')
        self.compare_groupbox.setLayout(self.compare_vbox)

        # create analyse_window_body_widget
        self.analyse_window_body_splitter = QSplitter(Qt.Vertical)
        #self.analyse_window_body_splitter.setLayout(self.analyse_window_body_vbox)
        self.analyse_window_body_splitter.addWidget(self.stats_groupbox)
        self.analyse_window_body_splitter.addWidget(self.compare_groupbox)

        #stats_groupbox_size_policy = QSizePolicy(self.stats_groupbox.sizePolicy())
        #print(stats_groupbox_size_policy.Policy())
        compare_groupbox_size_policy = QSizePolicy(self.compare_groupbox.sizePolicy())
        compare_groupbox_size_policy.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        #print(compare_groupbox_size_policy.Policy())
        self.compare_groupbox.setSizePolicy(compare_groupbox_size_policy)
        #self.compare_groupbox.setMinimumWidth(200)

        # set up body vbox
        self.analyse_window_vbox = QVBoxLayout()
        self.analyse_window_vbox.addWidget(self.analyse_window_body_splitter)

        self.setWindowTitle('Analyse Window')
        self.setLayout(self.analyse_window_vbox)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    analyse_window = analyseWindow()
    #analyse_window.setLayout(analyse_window.analyse_window_body_vbox)
    analyse_window.show()
    sys.exit(app.exec_())