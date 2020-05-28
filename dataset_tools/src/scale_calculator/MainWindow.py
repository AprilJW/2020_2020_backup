import os
import time
import copy
from enum import Enum
from PIL import Image
from PyQt5.Qt import QPixmap
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from scale_calculator import UI_MainWindow as ui
from canvas import Canvas


class Func(Enum):
    CALC_S_SEED = 's_seed'
    CALC_S_ROI = 's_roi'
    CALC_R_REF = 'r_ref'

FORM = '.3f'
REF_IMG_EXT = '.jpg'


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = ui.Ui_MainWindow()
        self.ui.setupUi(self)

        self.canvas = Canvas(self.ui.scrollArea)
        self.canvas.roiSelected.connect(self.on_roi_received)
        self.canvas.enable_drawing_roi = True

        self.ui.scrollArea.setWidget(self.canvas)
        self.ui.scrollArea.setWidgetResizable(True)
        
        self.ui.calcSeedScale.toggled.connect(self.update_gui)
        self.ui.calcRoiScale.toggled.connect(self.update_gui)
        self.ui.calcRref.toggled.connect(self.update_gui)
        
        self.update_gui()
        
    @pyqtSlot()
    def on_openFile_clicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Choose Image', ".")
        if isinstance(filename, (tuple, list)):
            filename = filename[0]
            if filename:
                self.load_file(filename)

    def load_file(self, filepath=None):
        self.setWindowTitle(filepath)
        with Image.open(filepath) as im:
            self.canvas.setImage(copy.deepcopy(im), calc_pixel_value=False)
        self.canvas.loadPixmap(QPixmap(filepath), [])

    @pyqtSlot()
    def on_saveResult_clicked(self):
        if not self.canvas.pil_img or not self.result.text():
            QMessageBox.information(self, 'Serious?', 'Nothing to save')
            return
        filename = self.cur_func.value
        reply = QMessageBox.question(self, 'Confirm', 'Save ' + filename + '? (Existing result will be overwritten)', 
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        fullpath = os.path.join(os.path.curdir, 'scale_calculator', filename)
        with open(fullpath, 'w') as f:
            f.write(self.result.text() + time.strftime('  (%Y-%m-%d %H:%M:%S)', time.localtime()))
        self.saveRrefImage(fullpath + REF_IMG_EXT)
    
    def saveRrefImage(self, fullpath):
        if self.cur_func != Func.CALC_R_REF:
            return
        r = int(self.ui.ruler.text())
        x, y, w, h = self.ui.roi.value()
        if r == 0 or w == 0 or h == 0:
            return
        
        size = self.ui.imageSize.value()
        ref_img = Image.new('RGB', (size, size))
        
        roi_img = self.canvas.pil_img.crop((x, y, x+w, y+h))
        ratio = min(size/w, size/h)
        w, h = int(w*ratio), int(h*ratio)
        roi_img = roi_img.resize((w, h))
        
        ref_img.paste(roi_img, (int((size-w)/2), int((size-h)/2)))
        ref_img.save(fullpath)
    
    @pyqtSlot()
    def on_loadRref_clicked(self):
        fullpath = os.path.join(os.path.curdir, 'scale_calculator', Func.CALC_R_REF.value)
        if not os.path.isfile(fullpath) or not os.path.isfile(fullpath + REF_IMG_EXT):
            QMessageBox.information(self, 'Serious?', 'No existing r_ref found')
            return
        with open(fullpath, 'r') as f:
            content = f.readline()
            value = content.split(' ')[0].strip()
            self.ui.Rref.setText(value)
        with Image.open(fullpath + REF_IMG_EXT) as im:
            self.ui.imageSize.setValue(im.size[0])
        
    @pyqtSlot(int)
    def on_imageSize_valueChanged(self):
        self.calc_r_ref()
    
    @pyqtSlot(float)
    def on_seedScaleRange_valueChanged(self, r):
        if len(self.ui.seedScale.text()) == 0:
            return
        seed_scale_for_2d = float(self.ui.seedScale.text()) - 1
        self.ui.seedScaleLow.setText(format(seed_scale_for_2d - r / 2, FORM))
        self.ui.seedScaleHigh.setText(format(seed_scale_for_2d + r / 2, FORM))

    def on_roi_received(self, rect):
        if not self.canvas.pil_img:
            return
        
        if self.ui.selectRuler.isChecked():
            ruler_size = int((rect.width()**2 + rect.height()**2)**(.5))
            self.ui.ruler.setText(str(ruler_size))
        else:
            self.ui.roi.setValue(rect.x(), rect.y(), rect.width(), rect.height())
            region = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            roi_img = self.canvas.pil_img.crop(region)
            roi_img.show()

        self.calc()

    def ruler_ratio(self):
        r_cur = int(self.ui.ruler.text())
        if len(self.ui.Rref.text()) == 0:
            return None
        r_ref = int(self.ui.Rref.text())
        return r_ref / r_cur if r_cur != 0 else None
    
    def roi_ratio(self):
        dl_image_size = self.ui.imageSize.value()
        _, _, w, h = self.ui.roi.value()
        return dl_image_size / max(w, h) if max(w, h) != 0 else None
        
    def calc_r_ref(self):
        roi_ratio = self.roi_ratio()
        if roi_ratio:
            r_cur = int(self.ui.ruler.text())
            r_ref = int(r_cur * roi_ratio)
            self.ui.Rref.setText(str(r_ref))

    def calc_s_seed(self):
        s_seed = self.ruler_ratio()
        if s_seed:
            self.ui.seedScale.setText(format(s_seed, FORM))
            self.on_seedScaleRange_valueChanged(self.ui.seedScaleRange.value())
    
    def calc_s_roi(self):
        s_roi_ideal = self.ruler_ratio()
        s_roi_limit = self.roi_ratio()
        if s_roi_ideal and s_roi_limit:
            s_roi = min(s_roi_ideal, s_roi_limit)
            self.ui.roiScale.setText(format(s_roi, FORM))

    def update_cur_func(self):       
        if self.ui.calcSeedScale.isChecked():
            self.cur_func = Func.CALC_S_SEED
            self.calc = self.calc_s_seed
            self.result = self.ui.seedScale
        elif self.ui.calcRoiScale.isChecked():
            self.cur_func = Func.CALC_S_ROI
            self.calc = self.calc_s_roi
            self.result = self.ui.roiScale
        elif self.ui.calcRref.isChecked():
            self.cur_func = Func.CALC_R_REF
            self.calc = self.calc_r_ref
            self.result = self.ui.Rref
        else:
            raise ValueError('WTF!')
    
    def update_gui(self):       
        self.update_cur_func()
        # roi
        visible = self.cur_func != Func.CALC_S_SEED
        self.ui.selectRoi.setVisible(visible)
        self.ui.roi.setVisible(visible)
        self.ui.roi.setValue(0, 0, 0, 0)
        # ruler
        self.ui.selectRuler.setChecked(True)
        self.ui.ruler.setText('0')
        # image size
        visible = self.cur_func == Func.CALC_R_REF
        self.ui.labelImageSize.setVisible(visible)
        self.ui.imageSize.setVisible(visible)
        # S_seed
        visible = self.cur_func == Func.CALC_S_SEED
        self.ui.labelSeedScale.setVisible(visible)
        self.ui.seedScale.setVisible(visible)
        self.ui.seedScale.setText('')
        self.ui.seedScaleLow.setText('')
        self.ui.seedScaleHigh.setText('')
        self.ui.for2dTool.setVisible(visible)
        # S_roi
        visible = self.cur_func == Func.CALC_S_ROI
        self.ui.labelRoiScale.setVisible(visible)
        self.ui.roiScale.setVisible(visible)
        self.ui.roiScale.setText('')
        