############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QApplication,
                             QVBoxLayout, QLabel, QFrame)
from PyQt5.QtGui import QPixmap, QPalette


class checkByPressLabel(QLabel):

    checker = pyqtSignal()

    def __init__(self, pixmap, qt_frame_shape=QFrame.Box,
                       qt_shadow_style=QFrame.Plain,
                       qt_color=Qt.yellow,
                       line_width=3):

        super().__init__()

        self.pixmap = pixmap
        self.raw_width = pixmap.width()
        self.raw_height = pixmap.height()
        self.checkedFlag = False
        self.checker.connect(lambda: self.labelOnClicked(
                qt_frame_shape, qt_shadow_style, qt_color, line_width)) #lambda: self.setQFrameColor(Qt.yellow)

    def mousePressEvent(self, event):
        self.checker.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            raw_image_pixmap = self.pixmap
            raw_image_label = QLabel()
            raw_image_label.setPixmap(raw_image_pixmap.scaled(self.raw_width, self.raw_height, Qt.KeepAspectRatio))

            self.show_raw_image_window = QWidget()
            window_vbox = QVBoxLayout()
            window_vbox.addWidget(raw_image_label)
            self.show_raw_image_window.setLayout(window_vbox)
            self.show_raw_image_window.setWindowTitle('Raw Image')
            self.show_raw_image_window.show()

    def isChecked(self):
        return self.checkedFlag

    def labelOnClicked(self, qt_frame_shape, qt_shadow_style, qt_color, line_width):
        if self.checkedFlag:
            self.checkedFlag = False
            self.setQFrameStyle(QFrame.NoFrame, qt_shadow_style, qt_color, line_width)
        else:
            self.checkedFlag = True
            self.setQFrameStyle(qt_frame_shape, qt_shadow_style, qt_color, line_width)

    def setQFrameStyle(self, qt_frame_shape, qt_shadow_style, qt_color, line_width):

        self.setFrameStyle(qt_frame_shape | qt_shadow_style)
        self.setLineWidth(line_width)

        color_palette = QPalette()
        color_palette.setColor(QPalette.Foreground, qt_color)
        self.setPalette(color_palette)


class displayWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 290, 150)
        image_pixmap = QPixmap('redrock_1.jpg')
        image_label = checkByPressLabel(image_pixmap)
        image_label.setPixmap(image_label.pixmap.scaled(300, 300, Qt.KeepAspectRatio))

        body_vbox = QVBoxLayout()
        body_vbox.addWidget(image_label)

        self.setLayout(body_vbox)
        self.setWindowTitle('Check by Press Label')
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    check_by_press_label = displayWindow()
    #analyse_window.setLayout(analyse_window.analyse_window_body_vbox)
    check_by_press_label.show()
    sys.exit(app.exec_())
