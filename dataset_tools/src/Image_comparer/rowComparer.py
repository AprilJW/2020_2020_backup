############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QPushButton, QFileDialog, QScrollArea)
from PyQt5.QtGui import QPixmap

class rowComparer(QWidget):

    def __init__(self):

        super().__init__()

    def setupWidget(self, display_width, display_height, save_width, save_height):

        self.display_width = display_width
        self.display_height = display_height
        self.save_width = save_width
        self.save_height = save_height

        # fill the layout
        self.display_grid_layout = self.fillGridLayout(display_width, display_height)
        self.save_grid_layout = self.fillGridLayout(save_width, save_height)

        # create display image widget
        self.display_image_widget = QWidget()
        self.display_image_widget.setLayout(self.display_grid_layout)
        #self.display_image_pixmap = self.display_image_widget.grab()

        # create save image widget
        self.save_image_widget = QWidget()
        self.save_image_widget.setLayout(self.save_grid_layout)
        self.save_image_pixmap = self.save_image_widget.grab()

        # set up scrollArea for the compare widget
        self.analyse_window_scroll_area = QScrollArea()
        self.analyse_window_scroll_area.setWidget(self.display_image_widget)
        self.analyse_window_scroll_area.setWidgetResizable(True)

        #print("check max size")
        #print(self.analyse_window_scroll_area.maximumHeight())
        #print(self.analyse_window_scroll_area.maximumWidth())
        #self.compare_frame.setFrameStyle(QFrame.WinPanel | QFrame.Raised)
        #self.compare_frame.setLineWidth(3)
        #self.analyse_window_scroll_area.setWidgetResizable(True)

        # create button hbox
        self.button_hbox = QHBoxLayout()

        # create "save" push button
        self.save_button = QPushButton('Save')

        # add pushbutton to the button_hbox
        self.button_hbox.addStretch(1)
        self.button_hbox.addWidget(self.save_button)

        # set up event for save_button
        self.save_button.clicked.connect(self.buttonClickedSave)

        # set up body_vbox
        self.body_vbox = QVBoxLayout()
        self.body_vbox.addWidget(self.analyse_window_scroll_area)
        self.body_vbox.addLayout(self.button_hbox)

        # set up layout
        self.setLayout(self.body_vbox)

    def fillGridLayout(self, image_width=100, image_height=100):

        grid_layout = QGridLayout()

        # create QPixmaps
        pixmap_1 = QPixmap('redrock_1.jpg')
        pixmap_2 = QPixmap('redrock_2.jpg')
        pixmap_3 = QPixmap('redrock_2.jpg')
        pixmap_4 = QPixmap('redrock_1.jpg')

        # create image_labels
        image_label_1 = QLabel()
        image_label_2 = QLabel()
        image_label_3 = QLabel()
        image_label_4 = QLabel()

        # set pixmap for image_labels
        image_label_1.setPixmap(pixmap_1.scaled(image_width, image_height))
        image_label_2.setPixmap(pixmap_2.scaled(image_width, image_height))
        image_label_3.setPixmap(pixmap_3.scaled(image_width, image_height))
        image_label_4.setPixmap(pixmap_4.scaled(image_width, image_height))

        # create text labels
        text_label_1 = QLabel('image1')
        text_label_2 = QLabel('image2')
        text_label_3 = QLabel('image3')
        text_label_4 = QLabel('image4')

        # fill grid_layout
        grid_layout.addWidget(image_label_1, 0, 0)
        grid_layout.addWidget(image_label_2, 0, 1)
        grid_layout.addWidget(text_label_1, 1, 0)
        grid_layout.addWidget(text_label_2, 1, 1)
        grid_layout.addWidget(image_label_3, 2, 0)
        grid_layout.addWidget(image_label_4, 2, 1)
        grid_layout.addWidget(text_label_3, 3, 0)
        grid_layout.addWidget(text_label_4, 3, 1)

        widget_index = grid_layout.indexOf(image_label_4)
        print(widget_index)
        pos = grid_layout.getItemPosition(widget_index)
        print(pos)

        return grid_layout

    def buttonClickedSave(self):

        print('Enter slot')
        save_file_name = QFileDialog().getSaveFileName(self, "Save as...", "name", "PNG (*.png);; BMP (*.bmp);;TIFF (*.tiff *.tif);; JPEG (*.jpg *.jpeg)")
        print(save_file_name)
        self.save_image_pixmap.save(save_file_name[0])

if __name__ == '__main__':

    app = QApplication(sys.argv)
    row_comparer_window = rowComparer()
    row_comparer_window.setupWidget(100,100,300,300)
    row_comparer_window.show()
    sys.exit(app.exec_())