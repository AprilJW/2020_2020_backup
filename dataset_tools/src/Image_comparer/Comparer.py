import sys
import os
import math
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from ui.MultiSelectDirDialog import MultiSelectDirDialog
import matplotlib
from PyQt5.Qt import QSizePolicy
from PyQt5 import QtCore
matplotlib.use('Qt5Agg')

from Image_comparer.analyseWindow import analyseWindow
from Image_comparer.figureCanvas import figureCanvas
from Image_comparer.rowComparer import rowComparer
from Image_comparer.checkByPressLabel import checkByPressLabel

class Comparer(QWidget):

    def __init__(self, number_of_initial_directories = 3):
        super().__init__()
        self.widget_id_generate_list = list(range(100000))
        self.widget_id_generate_list.reverse()
        self.initUI(number_of_initial_directories)

    def initUI(self, number_of_initial_directories):

        '''
        Create header
        '''
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.multi_select_dialog = MultiSelectDirDialog(self)
        self.verticalLayout.addWidget(self.multi_select_dialog)

        self.multi_select_dialog.setMinimumSize(QtCore.QSize(400, 0))
        self.multi_select_dialog.setMaximumSize(QtCore.QSize(16777215, 100))

        self.button_hbox = QHBoxLayout()
        self.button_hbox.addStretch(1)
        self.compare_button = QPushButton('Compare')
        self.button_hbox.addWidget(self.compare_button)
        self.verticalLayout.addLayout(self.button_hbox)

        self.main_window_grid_layout = QGridLayout()
        self.verticalLayout.addLayout(self.main_window_grid_layout)
        self.setLayout(self.verticalLayout)
        self.compare_button.clicked.connect(self.buttonClickedCompare)
        DesktopWidth = QDesktopWidget().availableGeometry().width()
        minimum_size = self.minimumSize()
        self.makeCenter(DesktopWidth * 0.25, minimum_size.width())
        self.setWindowTitle('Comparer')
        self.show()
        self.compared_flag = False

    def makeCenter(self, minimum_width, minimum_height):
        centerPoint = QDesktopWidget().availableGeometry().center()
        self.setMinimumWidth(minimum_width)
        self.setMinimumHeight(minimum_height)
        qtRectangle = self.geometry()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def buttonClickedCompare(self):
        number_existing_directories = len(self.multi_select_dialog.selected_dirs())
        self.image_name_lists = self.getImageNameLists()
        self.image_name_array = np.asarray(self.image_name_lists).transpose()
        print(self.image_name_array.shape)
        if len(self.image_name_array.shape) < 2 or self.image_name_array.shape[0] == 0 :
            QMessageBox.warning(self, 'Error Message', 'The dimension of each directory does not match, please check if the directory is empty or each directory has same number of images.')
            return 0
        if self.compared_flag:
            recompare_flag = QMessageBox.question(self, "Recompare Dialog", "Are you sure you want to Re-compare?")
            if recompare_flag == QMessageBox.Yes:
                self.current_page_scroll_area.hide()
                self.main_window_grid_layout.removeWidget(self.current_page_scroll_area)
            else:
                return 0
        else:
            self.analyse_button = QPushButton('Analyse')
            self.button_hbox.addWidget(self.analyse_button)
            self.analyse_button.clicked.connect(self.buttonClickedAnalyse)
            self.select_images = QCheckBox()
            self.select_images.stateChanged.connect(self.select_all_row_checker)
            self.button_hbox.addWidget(self.select_images)

        self.display_width = 300
        self.display_height = 300
        available_geometry = QDesktopWidget().availableGeometry()
        available_width = available_geometry.width()
        available_height = available_geometry.height()
        self.makeCenter(min((self.display_width + 40) * number_existing_directories + 80, available_width),
                        min(80 * number_existing_directories + 2 * self.display_height, available_height))
        self.directory_names = []
        self.pixmap_lists = []
        self.image_label_lists = []
        self.row_checker_list = []
        for index, widget_id in enumerate(self.multi_select_dialog.selected_dirs()):
            pixmap_list, image_label_list = self.readFolderImages(
                    index, widget_id, self.display_width, self.display_height)
            self.pixmap_lists.append(pixmap_list)
            self.image_label_lists.append(image_label_list)
        self.pixmap_array = np.asarray(self.pixmap_lists).transpose()
        self.image_label_array = np.asarray(self.image_label_lists).transpose()
        self.checkbox_stats_array = np.zeros_like(self.pixmap_array)
        self.compare_body_width = self.pixmap_array.shape[1]
        self.compare_body_height = self.pixmap_array.shape[0]
        self.row_checker_stats_array = np.zeros(self.compare_body_height)
        for row in range(self.compare_body_height):
            self.row_checker_checkbox = QCheckBox()
            self.row_checker_checkbox.stateChanged.connect(self.changeRowCheckerCheckboxStats)
            self.row_checker_list.append(self.row_checker_checkbox)
        self.row_checker_array = np.asarray(self.row_checker_list)
        self.images_per_page = 100
        self.number_of_pages = math.ceil(self.compare_body_height/self.images_per_page)
        self.current_page_layout = self.drawComparePage(1)
        self.compared_flag = True

    def select_all_row_checker(self):
        for i in self.row_checker_list:
            i.setChecked(self.select_images.isChecked())

    def buttonClickedGoToPage(self):
        goto_page_index = int(self.goto_page_index_lineEdit.text())
        if goto_page_index != self.current_page_index:
            self.drawComparePage(goto_page_index)

    def buttonClickedPreviousPage(self):
        previous_page_index = self.current_page_index - 1
        self.drawComparePage(previous_page_index)

    def buttonClickedNextPage(self):
        next_page_index = self.current_page_index + 1
        self.drawComparePage(next_page_index)

    def drawComparePage(self, page_index):
        page_layout = self.drawPageLayout(page_index)
        if page_layout:
            if self.compared_flag:
                self.main_window_grid_layout.removeWidget(self.current_page_scroll_area)
                self.main_window_grid_layout.removeWidget(self.page_choose_hbox_widget)
                self.page_choose_hbox_widget.hide()
                self.current_page_scroll_area.hide()
            self.current_page_layout = page_layout
            self.current_page_layout_widget = QWidget()
            self.current_page_layout_widget.setLayout(self.current_page_layout)
            self.current_page_scroll_area = QScrollArea()
            self.current_page_scroll_area.setWidget(self.current_page_layout_widget)
            self.main_window_grid_layout.addWidget(self.current_page_scroll_area, 1, 0)
            self.goto_page_index_lineEdit = QLineEdit('{0}'.format(self.current_page_index))
            self.number_of_pages_label = QLabel('/{0}'.format(self.number_of_pages))
            self.goto_page_button = QPushButton('Go to')
            self.previous_page_button = QPushButton('Previous')
            self.next_page_button = QPushButton('Next')
            self.goto_page_button.clicked.connect(self.buttonClickedGoToPage)
            self.previous_page_button.clicked.connect(self.buttonClickedPreviousPage)
            self.next_page_button.clicked.connect(self.buttonClickedNextPage)
            self.page_choose_hbox = QHBoxLayout()
            self.page_choose_hbox.addStretch(1)
            self.page_choose_hbox.addWidget(self.goto_page_index_lineEdit)
            self.page_choose_hbox.addWidget(self.number_of_pages_label)
            self.page_choose_hbox.addWidget(self.goto_page_button)
            self.page_choose_hbox.addWidget(self.previous_page_button)
            self.page_choose_hbox.addWidget(self.next_page_button)
            self.page_choose_hbox_widget = QWidget()
            self.page_choose_hbox_widget.setLayout(self.page_choose_hbox)
            self.main_window_grid_layout.addWidget(self.current_page_scroll_area, 1, 0)
            self.main_window_grid_layout.addWidget(self.page_choose_hbox_widget, 2, 0)

    def drawPageLayout(self, page_index):
        if page_index > self.number_of_pages or page_index < 1:
            QMessageBox.warning(self, "Error Message", "No such page, page index is out of bound.")
            self.goto_page_index_lineEdit.setText(str(self.current_page_index))
            return 0
        page_grid_layout = QGridLayout()
        for index, directory_name in enumerate(self.directory_names):
            page_grid_layout.addWidget(QLabel(directory_name), 0, index)
        page_grid_layout.addWidget(QLabel('Row Checker'), 0, self.compare_body_width)
        for row_index in range((self.compare_body_height - 1) % self.images_per_page + 1 if page_index == self.number_of_pages else self.images_per_page):
            overall_row_index = self.images_per_page * (page_index - 1) + row_index
            for column_index in range(self.compare_body_width):
                overall_column_index = column_index
                image_label = self.image_label_array[overall_row_index][overall_column_index]
                page_grid_layout.addWidget(image_label, 2 * row_index + 1, column_index)
                image_name = self.image_name_array[overall_row_index][overall_column_index]
                image_name_label = QLabel(image_name)
                page_grid_layout.addWidget(image_name_label, 2 * row_index + 2, column_index)
            page_grid_layout.addWidget(self.row_checker_list[overall_row_index],
                                                   2 * row_index + 1, self.compare_body_width, 2, 1)
            self.current_page_index = page_index
        return page_grid_layout

    def buttonClickedAnalyse(self):
        if np.sum(self.row_checker_stats_array) == 0:
            QMessageBox.warning(self, 'Error Message', 'You have not selected any row to compare, please select at least 1 row by ticking rowChecker checkbox.')
            return 0
        self.analyse_window = analyseWindow()
        stats_text_widget = self.statsTextWidget()
        self.analyse_window.stats_hbox.addWidget(stats_text_widget)
        stats_plot_widget = self.drawGraphMatplotlib()
        stats_plot_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.analyse_window.stats_hbox.addWidget(stats_plot_widget)
        row_comparer_widget = self.drawRowCompareWidget()
        self.analyse_window.compare_vbox.addWidget(row_comparer_widget)
        self.analyse_window.setMinimumWidth(self.compare_body_width *
                                            (row_comparer_widget.display_width + 10) + 60)
        self.analyse_window.show()

    def drawRowCompareWidget(self):
        class rowComparerWidget(rowComparer):
            def __init__(self):
                super().__init__()
            def fillGridLayout(self, image_width, image_height):
                grid_layout = QGridLayout()
                for index, directory_name in enumerate(self.directory_names):
                    grid_layout.addWidget(QLabel(directory_name), 0, index)
                for pixmap in np.nditer(self.pixmap_array, flags=['refs_ok']):
                    pos = np.where(self.pixmap_array == pixmap)
                    pos_x = int(pos[0])
                    pos_y = int(pos[1])
                    pixmap = pixmap.item(0)
                    image_label = QLabel()
                    image_label.setPixmap(pixmap.scaled(image_width, image_height, Qt.KeepAspectRatio))
                    grid_layout.addWidget(image_label, pos_x*2+1, pos_y)
                    image_name = self.image_name_array[pos].item(0)
                    image_name_label = QLabel(image_name)
                    grid_layout.addWidget(image_name_label, pos_x*2+2, pos_y)
                return grid_layout
        row_comparer_widget = rowComparerWidget()
        display_width = self.display_width/2
        display_height = self.display_height/2
        save_width = self.raw_width
        save_height = self.raw_height
        row_comparer_widget.directory_names = self.directory_names
        row_comparer_widget.pixmap_array = self.pixmap_array
        row_comparer_widget.pixmap_array = row_comparer_widget.pixmap_array[np.where(self.row_checker_stats_array)]
        row_comparer_widget.image_name_array = self.image_name_array
        row_comparer_widget.image_name_array = row_comparer_widget.image_name_array[np.where(self.row_checker_stats_array)]
        row_comparer_widget.setupWidget(display_width, display_height, save_width, save_height)
        return row_comparer_widget

    def statsTextWidget(self):
        stats_text_widget = QWidget()
        stats_text_vbox = QVBoxLayout()
        stats_text_vbox.addWidget(QLabel('Number of directories: {0}'.format(len(self.multi_select_dialog.selected_dirs()))), 1)
        stats_text_vbox.addWidget(QLabel('Number of images in each directory: {0}'.format(len(self.pixmap_lists[0]))), 1)
        stats_text_vbox.addWidget(QLabel('Total number of good results selected: {0}'.format(np.sum(self.checkbox_stats_array))), 1)
        stats_text_vbox.addWidget(QLabel('Total number of rows selected: {0}'.format(np.sum(self.row_checker_stats_array))), 1)
        stats_text_vbox.addStretch(5)
        stats_text_widget.setLayout(stats_text_vbox)
        return stats_text_widget

    def drawGraphMatplotlib(self):
        class analyseFigureCanvas(figureCanvas):
            def __init__(self, width=5, height=4, dpi=100):
                super().__init__(width=5, height=4, dpi=100)
                self.x = np.arange(4)
                self.heights = [1.5e5, 2.5e6, 5.5e6, 2.0e7]
                self.ticks = ['Bill', 'Fred', 'Mary', 'Sue']

            def draw_bar_plot(self):
                rects = self.axes.bar(self.x, self.heights, tick_label=self.ticks)
                self.autolabel(rects)
                self.axes.set_ylim([0,np.max(self.heights)+1])
                self.axes.set_title('number of good results for each directory')

            def autolabel(self, rects):
                for rect in rects:
                    height = rect.get_height()
                    self.axes.text(rect.get_x() + rect.get_width()/2., 1.02*height,
                            '%d' % int(height),
                            ha='center', va='bottom')
        analyse_figure_convas = analyseFigureCanvas(width=5, height=4, dpi=100)
        analyse_figure_convas.x = np.arange(len(self.multi_select_dialog.selected_dirs()))
        analyse_figure_convas.heights = np.sum(self.checkbox_stats_array, axis=0)
        analyse_figure_convas.ticks = self.directory_names
        analyse_figure_convas.draw_bar_plot()
        return analyse_figure_convas

    def getImageNameList(self, directory_path):
        file_extensions_tuple = ('.jpg', '.jpeg', '.gif', '.png', '.bmp')
        image_name_list = []
        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                if filename.endswith(file_extensions_tuple):
                    image_name_list.append(filename)
        # file name matching
        if image_name_list[0].split('.')[0].split('_')[-1].isdigit():
            image_name_list.sort(key=lambda x:int(x.split('.')[0].split('_')[-1]))
        else:
            image_name_list.sort(key=lambda x:int(x.split('.')[0].split('_')[-2]))
        return image_name_list

    def getImageNameLists(self):
        image_name_list = []
        directory_path_list = self.multi_select_dialog.selected_dirs()
        for directory_path in directory_path_list:
            image_name_list.append(self.getImageNameList(directory_path))
        return image_name_list

    def readFolderImages(self, index, widget_id, display_width, display_height):
        directory_path = widget_id
        directory_name = directory_path.split('/')[-1]
        self.directory_names.append(directory_name)
        image_name_list = self.image_name_lists[index]
        pixmap_list = []
        image_label_list = []
        for index, image_name in enumerate(image_name_list):
            image_path = os.path.join(directory_path, image_name)
            pixmap = QPixmap(image_path)
            pixmap_list.append(pixmap)
            image_label = checkByPressLabel(pixmap)
            image_label.setPixmap(pixmap.scaled(display_width, display_height, Qt.KeepAspectRatio))
            image_label.checker.connect(self.changeCheckboxStats)
            image_label_list.append(image_label)
        self.raw_width = pixmap_list[0].width()
        self.raw_height = pixmap_list[0].height()
        return pixmap_list, image_label_list

    def changeCheckboxStats(self):
        sender_checkbox = self.sender()
        array_pos = np.where(self.image_label_array == sender_checkbox)
        print(array_pos)
        if sender_checkbox.isChecked():
            self.checkbox_stats_array[array_pos] = 1
        else:
            self.checkbox_stats_array[array_pos] = 0
        print(self.checkbox_stats_array)
        print(np.sum(self.checkbox_stats_array))

    def changeRowCheckerCheckboxStats(self):
        sender_row_checker = self.sender()
        array_pos = np.where(self.row_checker_array == sender_row_checker)
        print(array_pos)
        if sender_row_checker.isChecked():
            self.row_checker_stats_array[array_pos] = 1
        else:
            self.row_checker_stats_array[array_pos] = 0
        print(self.row_checker_stats_array)
        print(np.sum(self.row_checker_stats_array))
	
def main():
    app = QApplication(sys.argv)
    ex = Comparer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
