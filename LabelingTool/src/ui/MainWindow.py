from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import QMessageBox
#!/usr/bin/env python
# -*- coding: utf8 -*-
import os.path
import re
import sys
import traceback
import math
import json
import cv2
import numpy as np
from functools import partial
from collections import defaultdict
from tqdm import tqdm
import xml.etree.ElementTree as ET  

from libs.shape import Shape, DEFAULT_LINE_COLOR
from libs.canvas import Canvas
from libs.canvas import WAIT_CURSOR
from libs.labelFile import LabelFile, LabelFileError
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import XML_EXT
import ui.UI_MainWindow as ui

__appname__ = "LabelTool"
FONT_SELECTED = QFont("Times", 15, QFont.Bold)
FONT_NORMAL = QFont("Times", 15, QFont.Normal)
# PyQt5: TypeError: unhashable type: 'QListWidgetItem'
class HashableQListWidgetItem(QListWidgetItem):

    def __init__(self, *args):
        super(HashableQListWidgetItem, self).__init__(*args)

    def __hash__(self):
        return hash(id(self))
               
class MainWindow(QMainWindow):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.canvas = Canvas(self.ui.scrollArea)
 
        self.canvas.zoomRequest.connect(self.zoomRequest)
        self.canvas.scrollRequest.connect(self.scrollRequest)
        self.canvas.newShape.connect(self.newShape)
        self.canvas.changeLabel.connect(self.changeLabel)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)
        self.canvas.menu.addAction(self.ui.actionDelete_Shape)
        
        self.ui.fileList.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        self.ui.scrollArea.setWidget(self.canvas)
        self.ui.scrollArea.setWidgetResizable(True)
        
        self.ui.dock_params.setVisible(False)
        self.ui.dock_image_editing_operations.setVisible(True)
        self.ui.current_label.setStyleSheet("QLabel { color : red; }")
        self.ui.actionSave.setEnabled(True)
        self.ui.actionSave_As.setEnabled(False)
        
        self.updateFontSize(15)
            
        self.scrollBars = {
            Qt.Vertical: self.ui.scrollArea.verticalScrollBar(),
            Qt.Horizontal: self.ui.scrollArea.horizontalScrollBar()
        }
        
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }
        
        self.mImgList = []
        self.dirname = None
        self.lastOpenDir = None
        self.filePath = "."
        self.defaultSaveDir = None
        
        self.zoom_value = 100

        # Whether we need to save or not.
        self.dirty = False

        # Enble auto saving if pressing next
        self.autoSaving = True
        
        self.itemToShapes = {} #listWidgetItem: shape1, shape2, ...
        self.shapeToItem = {} #shape: listWidgetItem
        self.labelToItem = {} #label: listWidgetItem
        self.prevLabelText = ''
        self.labelInfoDict = {}
        
        #application state
        self.image_np = None
        self.image = QImage()
        self.recentFiles = []
        self.maxRecent = 7
        self.zoom_level = 100
        self.zoomMode = self.MANUAL_ZOOM
        self.fit_window = False
        
        self.usingPascalVocFormat = True
        self.loadPredefinedClasses(os.path.join(os.path.dirname(__file__), "predefined_labels.json"))
        self.initLabelList()
        self.initUndoAction()
        self.predefined_labels_num = 0


    @pyqtSlot()
    def on_actionOpen_triggered(self):
        self.openFile()
            
    @pyqtSlot()
    def on_actionOpen_Dir_triggered(self):
        opened = self.openDir()
        self.ui.actionSave.setEnabled(opened)
        self.ui.actionSave_As.setEnabled(opened)
        
    @pyqtSlot()
    def on_actionOpen_Recent_triggered(self):
        pass
        
    @pyqtSlot()
    def on_actionSave_triggered(self):
        self.saveFile()
        
    @pyqtSlot()
    def on_actionSave_As_triggered(self):
        self.saveFileAs()
        
    @pyqtSlot()
    def on_actionSave_Files_triggered(self):
        self.saveFiles()
        
    @pyqtSlot()
    def on_actionClose_triggered(self):
        self.closeFile()
        
    @pyqtSlot()
    def on_actionQuit_triggered(self):
        self.close()
        
    @pyqtSlot()
    def on_actionCreate_Shape_triggered(self):
        self.createShape()

    @pyqtSlot()
    def on_actionDelete_Shape_triggered(self):
        self.deleteSelectedShape()
        
    @pyqtSlot()
    def on_actionDelete_Label_triggered(self):
        self.deleteSelectedLabel()
        
    @pyqtSlot()
    def on_actionZoom_In_triggered(self):
        self.addZoom(10)
        
    @pyqtSlot()
    def on_actionZoom_Out_triggered(self):
        self.addZoom(-10)
        
    @pyqtSlot()
    def on_actionZoom_Original_triggered(self):
        self.setZoom(100)
        
    @pyqtSlot()
    def on_actionUpdate_Line_Width_triggered(self):
        self.updateShapesWidth()
    
    @pyqtSlot()
    def on_actionUpdate_Font_Size_triggered(self):
        point_size, result = QInputDialog.getInt(self, "Set Font Size", "Font Size", 15, 0, 100, 1)
        self.updateFontSize(point_size)
    
    @pyqtSlot()
    def on_actionFit_Window_triggered(self):
        self.setFitWindow(self.FIT_WINDOW)
    
    @pyqtSlot()
    def on_actionFit_Width_triggered(self):
        self.setFitWidth(self.FIT_WIDTH)
        
    @pyqtSlot()
    def on_actionClear_Canvas_triggered(self):
        self.clearCanvas()
        
    @pyqtSlot()
    def on_actionNext_Image_triggered(self):
        self.openNextImg()
    
    @pyqtSlot()
    def on_actionPrev_Image_triggered(self):
        self.openPrevImg()

    @pyqtSlot()
    def on_actionCheck_Label_triggered(self):
        if not isinstance(self.dirname, str):
            QMessageBox.warning(self, 'warning', 'Please select dir')
        else:
            self.get_label_info(self.dirname)

    @pyqtSlot(bool)
    def on_actionShow_Lable_List_triggered(self, checked):
        self.ui.dock_label.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionShow_File_List_triggered(self, checked):
        self.ui.dock_file_list.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionShow_Dilate_Params_triggered(self, checked):
        self.ui.dock_params.setVisible(checked)
    
    @pyqtSlot(QListWidgetItem)
    def on_labelList_itemActivated(self):
        self.labelSelectionChanged()
        
    @pyqtSlot()
    def on_labelList_itemSelectionChanged(self):
        self.labelSelectionChanged()
        
    @pyqtSlot(int)
    def on_zoomSlider_valueChanged(self, value): 
        if value == 0:
            return
        self.setZoom(100 + value)
        self.ui.zoomValue.setValue(value)

    @pyqtSlot(int)
    def on_eraser_strength_valueChanged(self, value):
        self.canvas.setEraserStrength(value)

    @pyqtSlot()
    def on_exit_image_editing_clicked(self):
        if self.ui.exit_image_editing.text() == 'Exit Image Editing':
            self.set_image_operations('label')
            self.canvas.mode = Canvas.EDIT
            self.ui.exit_image_editing.setText('Enter Image Editing')
            self.ui.crop.setDisabled(True)
            self.ui.reverse_crop.setDisabled(True)
            self.ui.magic_wand.setDisabled(True)
            self.ui.eraser_strength.setDisabled(True)
        else:
            self.set_image_operations('crop')
            self.ui.exit_image_editing.setText('Exit Image Editing')
            self.ui.crop.setDisabled(False)
            self.ui.reverse_crop.setDisabled(False)
            self.ui.magic_wand.setDisabled(False)
            self.ui.eraser_strength.setDisabled(False)

    @pyqtSlot()
    def on_crop_clicked(self):
        print('crop')
        self.set_image_operations('crop')
        self.canvas.cropping()

    @pyqtSlot()
    def on_reverse_crop_clicked(self):
        self.set_image_operations('crop')
        self.canvas.cropping(True)

    @pyqtSlot(bool)
    def on_magic_wand_clicked(self, checked):
        if checked:
            self.set_image_operations('magic_wand')
        else:
            self.set_image_operations('crop')

    def get_label_info(self, dir_path):
        labels_path = os.path.join(dir_path, 'labels')
        labels_exist_path = labels_path if os.path.exists(labels_path) else dir_path
        
        self.label_to_num = {}
        for file_name in tqdm(os.listdir(labels_exist_path), "check label"):
            if os.path.splitext(file_name)[1] != XML_EXT:
                continue
            xml_path = os.path.join(labels_exist_path, file_name)
            reader = PascalVocReader(xml_path)
            for shape in reader.shapes:
                if shape[0] not in self.label_to_num:
                    self.label_to_num.setdefault(shape[0], 1)
                else:
                    self.label_to_num[shape[0]] += 1
        list_of_dataset = os.listdir( dir_path)
        self.label_to_num['origin_image_num'] = 0
        self.label_to_num['labeled_image_num'] = 0
        for each_item in list_of_dataset:
            if os.path.splitext(each_item)[1] == '.jpg':
                self.label_to_num['origin_image_num'] += 1
            else:
                self.check_label_exist(os.path.join(dir_path, each_item))
        QMessageBox.information(None, 'info', str(self.label_to_num))
        
    def check_label_exist(self, xml_item):
        parser = ET.XMLParser(encoding="utf-8")
        tree = ET.parse(xml_item, parser)
        root = tree.getroot()
        check_object = root.find("./object")
        if check_object :
            self.label_to_num['labeled_image_num'] += 1
                  
    def set_image_operations(self, value):
        print('image opt', value)
        if value.lower() == 'crop':
            self.canvas.image_editing_status = Canvas.CROP
        elif value.lower() == "magic_wand":
            self.canvas.image_editing_status = Canvas.MAGIC_WAND
            self.canvas.mode = Canvas.ERASING
        else:
            self.canvas.image_editing_status = Canvas.LABEL

    def initUndoAction(self):
        undoAction = self.canvas.undoStack.createUndoAction(self, 'Undo')
        undoAction.setShortcuts(QKeySequence.Undo)
        icon = QIcon()
        icon.addPixmap(QPixmap("icons/undo.png"), QIcon.Normal, QIcon.Off)
        undoAction.setIcon(icon)
        self.ui.menuEdit.addAction(undoAction)
        self.ui.mainToolBar.addAction(undoAction)
        redoAction = self.canvas.undoStack.createRedoAction(self, 'Redo')
        redoAction.setShortcuts(QKeySequence.Redo)

    def noShapes(self):
        return not self.itemToShapes

    def toggleAdvancedMode(self, value=True):
        self.canvas.setEditing(True)
        self.populateModeActions()
        if value:
            self.actions.createMode.setEnabled(True)
            self.actions.editMode.setEnabled(False)
            self.dock.setFeatures(self.dock.features() | self.dockFeatures)
        else:
            self.dock.setFeatures(self.dock.features() ^ self.dockFeatures)

    def setDirty(self):
        self.dirty = True

    def setClean(self):
        self.dirty = False

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.itemToShapes.clear()
        self.shapeToItem.clear()
        self.ui.labelList.clear()
        self.filePath = None
        self.imageData = None
        self.labelFile = None
        self.canvas.resetState()

    def currentItem(self):
        items = self.ui.labelList.selectedItems()
        if items:
            return items[0]
        return None

    def addRecentFile(self, filePath):
        if filePath in self.recentFiles:
            self.recentFiles.remove(filePath)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filePath)

    def createShape(self):
        self.canvas.currentLabel = self.ui.current_label.text()
        self.canvas.setEditing(False)

    def toggleDrawingSensitive(self, drawing=True):
        """In the middle of drawing, toggling between modes should be disabled."""
        if not drawing:
            # Cancel creation.
            print('Cancel creation.')
            self.canvas.setEditing(True)
            self.canvas.restoreCursor()

    def toggleDrawMode(self, edit=True):
        self.canvas.setEditing(edit)
        self.actions.createMode.setEnabled(edit)
        self.actions.editMode.setEnabled(not edit)

    def setCreateMode(self):
        assert self.advanced()
        self.toggleDrawMode(False)

    def setEditMode(self):
        assert self.advanced()
        self.toggleDrawMode(True)

    def editLabel(self, item=None):
        if not self.canvas.editing():
            return
        item = item if item else self.currentItem()
        text, result = QInputDialog.getText(self, "Set Label Name", "Label Name", QLineEdit.Normal, '')
        if text is not None and result:
            item.setText(text)
            self.setDirty()
    
    def editShape(self, shape):
        pass

    # Tzutalin 20160906 : Add file list and dock to move faster
    def fileitemDoubleClicked(self, item=None):
        if len(self.canvas.shapes) > 0 and self.dirty:
            self.saveFile() 
        currIndex = self.mImgList.index(item.text())
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename)


    # React to canvas signals.
    def shapeSelectionChanged(self, selected=False):
        self.restore_list_style()
        shape = self.canvas.selectedShape
        if shape is None:
            return
        if shape in self.shapeToItem:
            blocked = self.ui.labelList.blockSignals(True)
            self.shapeToItem[shape].setSelected(True)
            self.shapeToItem[shape].setFont(FONT_SELECTED)
            self.ui.labelList.blockSignals(blocked)

    def addShapeList(self, shape):
        item = self.labelToItem[shape.label]

        try:
            self.itemToShapes[item].append(shape)
        except KeyError:
            self.itemToShapes[item] = []
            self.itemToShapes[item].append(shape)    
        
        self.shapeToItem[shape] = item
            
    def addLabel(self):
        text, result = QInputDialog.getText(self, "Set Label Name", "Label Name", QLineEdit.Normal, self.prevLabelText)

        if not text:
            return None
        if text in self.labelInfoDict.keys():
            return text   #label is exist
        item = HashableQListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        item.setSelected(True)
        self.ui.labelList.addItem(item)
        self.labelToItem[text] = item
        self.ui.labelList.setCurrentItem(item)
        self.itemToShapes[item] = []
        
        self.labelInfoDict[text] = (True, self.canvas.POLYGON, 
                                    self.canvas.LABEL_COLORS[int(len(self.labelInfoDict) % len(self.canvas.LABEL_COLORS))]) #name, isClosePath, polygon, enable
        return text
    
    def updateShapesWidth(self):
        lineWidth, result = QInputDialog.getInt(self, "Set LineWidth for all Shapes", "Line Width",
                                               1, 0, 100, 1)
        self.canvas.updateShapes(lineWidth)
        
    def updateFontSize(self, point_size):
        font = QFont()
        font.setPointSize(point_size)
        widgets = self.findChildren(QWidget)
        for w in widgets:
            w.setFont(font)
        self.update()
    
    def initLabelList(self):
        if self.labelInfoDict is None:
            return
        self.ui.labelList.clear()
        for label in self.labelInfoDict.keys():
            item = HashableQListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setSelected(True)
            self.ui.labelList.addItem(item)
            self.labelToItem[label] = item
        self.ui.labelList.setCurrentRow(0)

    def removeLabel(self, shape):
        if shape is None:
            return
        item = self.shapeToItem[shape]
        self.itemToShapes[item].remove(shape)
        if len(self.itemToShapes[item]) == 0:
            del self.itemToShapes[item]
        del self.shapeToItem[shape]   
    
    def loadLabels(self, shapes):    
        s = []
        self.initLabelList()
        idx = len(self.labelInfoDict)
        for label, lineWidth, points, ellipse_points, rotate, r1, r2, center in shapes:
            if label not in self.labelInfoDict.keys():
                with open(os.path.join(os.path.dirname(__file__), "predefined_labels.json")) as f:
                    predefined_json = json.load(f)
                    new_append_predefined_dict = {"name": "", "isPathClosed": True, "type": 0, "enable": True}
                    new_append_predefined_dict['name'] = label
                    if r1:
                        new_append_predefined_dict['type'] = 1
                    predefined_json['labels'].append(new_append_predefined_dict)
                with open(os.path.join(os.path.dirname(__file__), "predefined_labels.json"), "w") as f:
                    json.dump(predefined_json, f, indent=4)
                self.canvas.LABEL_COLORS.extend(self.canvas.random_colors(N=1))
                self.labelInfoDict[label] = (True, new_append_predefined_dict['type'],
                                                 self.canvas.LABEL_COLORS[idx])
                item = HashableQListWidgetItem(label)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setSelected(True)
                self.ui.labelList.addItem(item)
                self.labelToItem[label] = item
                idx = idx + 1
                    
            shape = Shape(label=label)
            shape.lineWidth = lineWidth
            shape.isPathClosed = self.labelInfoDict[label][0]
            shape.d_type = self.labelInfoDict[label][1]
            shape.lineColor = self.labelInfoDict[label][2]
            shape.rotate = rotate
            shape.r1 = r1
            shape.r2 = r2
            shape.center = center
            
            for x, y in points:
                shape.addPoint(QPointF(x, y))
            
            for x, y in ellipse_points:
                shape.ellipse_points.append(QPointF(x, y))

            if shape.d_type == self.canvas.Ellipse:
                shape.sampleEllipsePoints()               
            
            shape.close()
            s.append(shape)
            self.addShapeList(shape)

        self.canvas.loadShapes(s)
        
    def calcShapeParent(self, s):
        s.parentGuid = s.guid
        for shape in self.canvas.shapes:
            if shape.containsShape(s):
                s.parentGuid = shape.guid
                return  

    def saveLabels(self, annotationFilePath):
        annotationFilePath = annotationFilePath
        imgFileDir = os.path.dirname(annotationFilePath)
        imgFileName = os.path.basename(annotationFilePath)
        dataFileName = os.path.splitext(imgFileName)[0] + ".compressed"
        dataPath = os.path.join(imgFileDir, dataFileName)
        imgPath = os.path.join(imgFileDir, os.path.splitext(imgFileName)[0] + ".jpg")
        
        if self.labelFile is None:
            self.labelFile = LabelFile()
            self.labelFile.verified = self.canvas.verified

        def format_shape(s):
            self.calcShapeParent(s)
            return dict(label=s.label,
                        guid=s.guid,
                        parentGuid = s.parentGuid,
                        lineWidth=s.lineWidth,
                        rotate = s.rotate,
                        r1 = s.r1,
                        r2 = s.r2,
                        center = (s.center.x(), s.center.y()),
                        points=[(p.x(), p.y()) for p in s.points],
                        ellipse_points = [(p.x(), p.y()) for p in s.ellipse_points])

        shapes = [format_shape(shape) for shape in self.canvas.shapes]
        # Can add differrent annotation formats here
        try:
            if self.usingPascalVocFormat is True:
                print ('Img: ' + imgPath + ' -> Its xml: ' + annotationFilePath + ' -> label data file: ' + dataPath)
                labelNames = []
                for label in self.labelInfoDict.keys():
                    labelNames.append(label[0])
                self.labelFile.setLabels(labelNames)
                self.labelFile.savePascalVocFormat(annotationFilePath, shapes, imgPath, self.imageData)
                #for deeplearing, no need to save compress label data
                if self.ui.actionSave_Label_Compress_Data.isChecked():
                    self.labelFile.saveData(dataPath, self.canvas.shapes, imgPath, 
                                    (self.ui.cannyKSize.value(),self.ui.cannyKSize.value()), 
                                    (self.ui.boxKSize.value(), self.ui.boxKSize.value()), 
                                    (self.ui.labelKSize.value(), self.ui.labelKSize.value()),
                                    self.ui.actionSave_Rf_Data.isChecked())  #check if save random forest data file
            else:
                self.labelFile.save(annotationFilePath, shapes, imgPath, self.imageData)
            return True
        except LabelFileError as e:
            self.errorMessage(u'Error saving label data', u'<b>%s</b>' % e)
            return False

    def copySelectedShape(self):
        self.addShapeList(self.canvas.copySelectedShape())
        # fix copy and delete
        self.shapeSelectionChanged(True)
        
    def restore_list_style(self):
        for i in range(self.ui.labelList.count()):
            self.ui.labelList.item(i).setFont(FONT_NORMAL)

    def labelSelectionChanged(self):
        self.restore_list_style()
        item = self.currentItem()
        
        if item:
            if self.ui.fileList.currentItem() is not None:
                self.setWindowTitle(__appname__ + ' ' + self.ui.fileList.currentItem().text())
            item.setFont(FONT_SELECTED)
            self.ui.current_label.setText(item.text())
            label = item.text()
            labelInfo = self.labelInfoDict[label]
            self.canvas.currentLabel = label
            self.canvas.currentDType = labelInfo[1]
            try:
                shapes = []
                shapes = self.itemToShapes[item]
                self.canvas.selectShapes(shapes, label, labelInfo)
            except KeyError:
                self.canvas.deSelectShapes()
                print("no shape is in current label")

    def labelItemChanged(self, item):
        if self.itemToShapes is None:
            return
        self.ui.labelList.setCurrentItem(item)
        shape = self.itemToShapes[item]
        if item.text() != shape.label:
            shape.label = item.text()
            self.setDirty()
        else:  # User probably changed item visibility
            self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    # Callback functions:
    def newShape(self):
        text = self.ui.current_label.text()
        
        if text:
            self.prevLabelText = text
            shape = self.canvas.setLastLabel(text)
            shape.isPathClosed = self.labelInfoDict[text][0]
            shape.d_type = self.labelInfoDict[text][1]
            shape.label = text
            shape.lineColor = self.labelInfoDict[text][2]
            self.addShapeList(shape)
            self.setDirty()
        else:
            self.canvas.resetAllLines()

    def changeLabel(self, shape, change_item):
        if change_item not in list(self.labelInfoDict.keys()):
            QMessageBox.warning(self, 'check label', 'modified label not in Labels list')
        else:
            shape.label = change_item
            self.setDirty()
            
    def scrollRequest(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scrollBars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

    def setZoom(self, value):
        self.zoomMode = self.MANUAL_ZOOM
        self.setZoomValue(value)

    def addZoom(self, increment=10):
        self.setZoom(self.zoom_value + increment)

    def zoomRequest(self, delta):
        units = delta / (8 * 15)
        scale = 10
        self.addZoom(scale * units)

    def setFitWindow(self, value=True):
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()
        
    def clearCanvas(self):
        for shape in self.canvas.shapes:
            self.canvas.selectedShape = shape
            self.deleteSelectedShape()

    def togglePolygons(self, value):
        for item, shape in self.itemToShapes.items():
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def loadFile(self, filePath=None):
        """Load the specified file, or the last opened file if None."""
        self.canvas.setEnabled(False)
        if filePath is None:
            filePath = self.settings.get('filename')

        unicodeFilePath = filePath
        # Tzutalin 20160906 : Add file list and dock to move faster
        # Highlight the file item
        if unicodeFilePath and self.ui.fileList.count() > 0:
            index = self.mImgList.index(unicodeFilePath)
            fileWidgetItem = self.ui.fileList.item(index)
            fileWidgetItem.setSelected(True)

        if unicodeFilePath and os.path.exists(unicodeFilePath):
            if LabelFile.isLabelFile(unicodeFilePath):
                try:
                    self.labelFile = LabelFile(unicodeFilePath)
                except LabelFileError as e:
                    self.errorMessage(u'Error opening file',
                                      (u"<p><b>%s</b></p>"
                                       u"<p>Make sure <i>%s</i> is a valid label file.")
                                      % (e, unicodeFilePath))
                    self.status("Error reading %s" % unicodeFilePath)
                    return False
                self.imageData = self.labelFile.imageData
            else:
                # Load image:
                # read data first and store for saving into label file
                self.canvas.image_np = cv2.imread(unicodeFilePath) # read as 3-channel
                with open(unicodeFilePath, 'rb') as f:
                    self.imageData = f.read()
                self.labelFile = None
            image = QImage.fromData(self.imageData)
            if image.isNull():
                self.errorMessage(u'Error opening file',
                                  u"<p>Make sure <i>%s</i> is a valid image file." % unicodeFilePath)
                self.status("Error reading %s" % unicodeFilePath)
                return False
            self.status("Loaded %s" % os.path.basename(unicodeFilePath))
            self.image = image
            self.filePath = unicodeFilePath
            self.canvas.loadPixmap(QPixmap.fromImage(image))
            if self.labelFile:
                self.loadLabels(self.labelFile.shapes)
            self.setClean()
            self.canvas.setEnabled(True)
            self.paintCanvas()
            self.addRecentFile(self.filePath)
            
            # Label xml file and show bound box according to its filename
            if self.usingPascalVocFormat is True:
                if self.defaultSaveDir is not None:
                    basename = os.path.basename(
                        os.path.splitext(self.filePath)[0]) + XML_EXT
                    xmlPath = os.path.join(self.defaultSaveDir, basename)
                    self.loadPascalXMLByFilename(xmlPath)
                else:
                    xmlPath=os.path.splitext(self.filePath)[0] + XML_EXT
                    if os.path.isfile(xmlPath):
                        self.loadPascalXMLByFilename(xmlPath)

            self.setWindowTitle(__appname__ + ' ' + filePath)

            # Default : select last item if there is at least one item
            #if self.ui.labelList.count():
                #self.ui.labelList.setCurrentItem(self.ui.labelList.item(self.ui.labelList.count()-1))
                #self.ui.labelList.setItemSelected(self.ui.labelList.item(self.ui.labelList.count()-1), True)

            self.canvas.setFocus(True)
            return True
        return False

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)
        
    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.setZoomValue(value)
    
    def setZoomValue(self, value):
        self.zoom_value = value
        self.paintCanvas()

        
    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoom_value
        self.canvas.adjustSize()
        self.canvas.update()

    def scaleFitWindow(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def scanAllImages(self, folderPath):
        extensions = ['.jpeg', '.jpg', '.png', '.bmp']
        images = []

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relatviePath = os.path.join(root, file)
                    path = os.path.abspath(relatviePath)
                    images.append(path)
        images.sort(key=lambda x: x.lower())
        return images

    def changeSavedir(self, _value=False):
        if self.defaultSaveDir is not None:
            path = self.defaultSaveDir
        else:
            path = '.'

        dirpath = QFileDialog.getExistingDirectory(self,
                                                       '%s - Save to the directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                       | QFileDialog.DontResolveSymlinks)

        if dirpath is not None and len(dirpath) > 1:
            self.defaultSaveDir = dirpath

        self.statusBar().showMessage('%s . Annotation will be saved to %s' %
                                     ('Change saved folder', self.defaultSaveDir))
        self.statusBar().show()

    def openAnnotation(self, _value=False):
        if self.filePath is None:
            return

        path = os.path.dirname(self.filePath)\
            if self.filePath else '.'
        if self.usingPascalVocFormat:
            filters = "Open Annotation XML file (%s)" % \
                      ' '.join(['*.xml'])
            filename = QFileDialog.getOpenFileName(self,'%s - Choose a xml file' % __appname__, path, filters)
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]
            self.loadPascalXMLByFilename(filename)

    def openDir(self, _value=False):
        if not self.mayContinue():
            return False
        path = os.path.dirname(self.filePath if self.filePath else '.')

        if self.lastOpenDir is not None and len(self.lastOpenDir) > 1:
            path = self.lastOpenDir

        dirpath = QFileDialog.getExistingDirectory(self,
                                                     '%s - Open Directory' % __appname__, path,  QFileDialog.ShowDirsOnly
                                                     | QFileDialog.DontResolveSymlinks)

        if dirpath is not None and len(dirpath) > 1:
            self.lastOpenDir = dirpath

        self.dirname = dirpath

        self.filePath = None
        self.ui.fileList.clear()
        self.mImgList = self.scanAllImages(dirpath)
        self.openNextImg()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.ui.fileList.addItem(item)
            
        return True

    def verifyImg(self, _value=False):
        # Proceding next image without dialog if having any label
         if self.filePath is not None:
            try:
                self.labelFile.toggleVerify()
            except AttributeError:
                # If the labelling file does not exist yet, create if and
                # re-save it with the verified attribute.
                self.saveFile()
                self.labelFile.toggleVerify()

            self.canvas.verified = self.labelFile.verified
            self.paintCanvas()
            self.saveFile()

    def openPrevImg(self, _value=False):
        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        if self.filePath is None:
            return

        currIndex = self.mImgList.index(self.filePath)
        if currIndex - 1 >= 0:
            filename = self.mImgList[currIndex - 1]
            if filename:
                self.loadFile(filename)

    def openNextImg(self, _value=False):
        # Proceding next image without dialog if having any label
        print('image editing', self.canvas.image_editing_status)
        if self.canvas.image_editing_status != Canvas.LABEL:
            self.saveFile()

        if self.autoSaving and self.dirty and self.filePath:
            print("save file when open next img")
            self.saveFile()

        if not self.mayContinue():
            return

        if len(self.mImgList) <= 0:
            return

        filename = None
        if self.filePath is None:
            filename = self.mImgList[0]
        else:
            currIndex = self.mImgList.index(self.filePath)
            if currIndex + 1 < len(self.mImgList):
                filename = self.mImgList[currIndex + 1]

        if filename:
            self.loadFile(filename)

    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = os.path.dirname(self.filePath) if self.filePath else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.loadFile(filename)

    def saveFile(self, _value=False):
        if self.canvas.image_editing_status != Canvas.LABEL:
            filenameWithoutExtension = os.path.splitext(self.filePath)[0]
            dest_path = os.path.join(self.currentPath(), filenameWithoutExtension + '.png')
            b, g, r = cv2.split(self.canvas.image_np)
            gray = cv2.cvtColor(self.canvas.image_np, cv2.COLOR_BGR2GRAY)
            _, a = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
            a_large_canvas = np.zeros((a.shape[0]+200, a.shape[1]+200), np.uint8)
            a_large_canvas[100:100+a.shape[0], 100:100+a.shape[1]] = a
            a_large_canvas = cv2.erode(a_large_canvas, np.ones((3, 3), np.uint8), 1)
            a = a_large_canvas[100:100+a.shape[0], 100:100+a.shape[1]]
            image = cv2.merge([b, g, r, a])
            _, cnts, hier = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts_lens = map(lambda x: len(x), cnts)
            max_cnt_id = np.argmax(np.array(cnts_lens), axis=0)
            bndbox = cv2.boundingRect(cnts[max_cnt_id])
            image = image[bndbox[1]:bndbox[1]+bndbox[3], bndbox[0]:bndbox[0]+bndbox[2]]
            cv2.imwrite(dest_path, image)
        elif self.defaultSaveDir is not None and len(self.defaultSaveDir):
            if self.filePath:
                imgFileName = os.path.basename(self.filePath)
                prefix = os.path.splitext(imgFileName)[0]
                savedFileName = prefix + XML_EXT
                savedPath = os.path.join(self.defaultSaveDir, savedFileName)
                self._saveFile(savedPath)
        else:
            imgFileDir = os.path.dirname(self.filePath)
            imgFileName = os.path.basename(self.filePath)
            prefix = os.path.splitext(imgFileName)[0]
            savedFileName = prefix + XML_EXT
            savedPath = os.path.join(imgFileDir, savedFileName)
            dest_path = savedPath if self.labelFile else self.saveFileDialog()
            self._saveFile(dest_path)

    def saveFiles(self):   
        if self.ui.fileList.count() < 1:
            return
        
        for i in range(self.ui.fileList.count()):
            print('Saving file', i)
            item = self.ui.fileList.item(i)
            filePath = item.text()
            filedir, filename = os.path.split(filePath)
            filenamesplit = os.path.splitext(filename)
            savedFileName = filenamesplit[0] + XML_EXT
            savedPath = os.path.join(filedir, savedFileName)
            self.loadFile(filePath)
            if not self._saveFile(savedPath):
                break
                

    def saveFileAs(self, _value=False):
        if self.canvas.image_editing_status != Canvas.LABEL:
            dest_path = self.saveImageDialog()
            b, g, r = cv2.split(self.canvas.image_np)
            gray = cv2.cvtColor(self.canvas.image_np, cv2.COLOR_BGR2GRAY)
            _, a = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
            a = cv2.erode(a, np.ones((5, 5), np.uint8), 1)
            image = cv2.merge([b, g, r, a])
            cv2.imwrite(dest_path, image)
        else:
            assert not self.image.isNull(), "cannot save empty image"
            self._saveFile(self.saveFileDialog())

    def saveFileDialog(self):
        caption = '%s - Choose File' % __appname__
        filters = 'File (*%s)' % (LabelFile.suffix)
        openDialogPath = self.currentPath()
        dlg = QFileDialog(self, caption, openDialogPath, filters)
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        filenameWithoutExtension = os.path.splitext(self.filePath)[0]
        dlg.selectFile(filenameWithoutExtension)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            return dlg.selectedFiles()[0]
        return ''

    def saveImageDialog(self):
        caption = '%s - Choose File' % __appname__
        filters = 'File (*%s)' % ('.png')
        openDialogPath = self.currentPath()
        dlg = QFileDialog(self, caption, openDialogPath, filters)
        dlg.setDefaultSuffix('.png')
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        filenameWithoutExtension = os.path.splitext(self.filePath)[0]
        dlg.selectFile(filenameWithoutExtension)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            return dlg.selectedFiles()[0]
        return ''

    def checkShapes(self):
        contour_label = 'outer-contour'
        contours = [shape for shape in self.canvas.shapes if shape.label == contour_label]
        others = [shape for shape in self.canvas.shapes if shape.label != contour_label]

        violations = [[c1,c2] for c1 in contours for c2 in contours if c1.containsShape(c2)]
        if len(violations) > 0:
            self.canvas.selectShapes(violations[0], None, None)
            return 'Outer-contours should not contain another outer-contour\n外轮廓内部不能包含其它外轮廓'
        
        violations = [[c,o] for c in contours for o in others if c.intersectsWith(o)]
        if len(violations) > 0:
            self.canvas.selectShapes(violations[0], None, None)
            return 'Outer-contours should not intersect with non-outer-contours\n外轮廓与非外轮廓不能交叉'
        
        violations = [c for c in contours if c.containsNone(others)]
        if len(violations) > 0:
            self.canvas.selectShapes(violations, None, None)
            return 'Outer-contours should contain at least 1 non-outer-contour\n外轮廓内部至少包含1个非外轮廓'
        
        polygons = [shape for shape in others if shape.d_type == shape.S_POLYGON]
        violations = [[p1,p2] for p1 in polygons for p2 in polygons if p1 is not p2 and p1.intersectsWith(p2)]
        if len(violations) > 0:
            self.canvas.selectShapes(violations[0], None, None)
            return 'Non-outer-contour-polygons should not intersect with each other\n非外轮廓多边形不能互相交叉'
        return None        
        
    def _saveFile(self, annotationFilePath):
        #self.canvas.overrideCursor(WAIT_CURSOR)
        error_info = self.checkShapes()
        if error_info is not None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Save File Failed! Error:\n" + error_info)
            msg.exec_()
            return False
            
        if annotationFilePath and self.saveLabels(annotationFilePath):
            self.setClean()
            self.statusBar().showMessage('Saved to  %s' % annotationFilePath)
            self.statusBar().show()
        return True

    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    def mayContinue(self):
        return not (self.dirty and not self.discardChangesDialog())

    def discardChangesDialog(self):
        yes, no = QMessageBox.Yes, QMessageBox.No
        msg = u'You have unsaved changes, proceed anyway?'
        return yes == QMessageBox.warning(self, u'Attention', msg, yes | no)

    def errorMessage(self, title, message):
        return QMessageBox.critical(self, title,
                                    '<p><b>%s</b></p>%s' % (title, message))

    def currentPath(self):
        return os.path.dirname(self.filePath) if self.filePath else '.'

    def deleteSelectedShape(self):
        self.removeLabel(self.canvas.deleteSelected())
        self.setDirty()
        #if self.noShapes():
        #    for action in self.actions.onShapesPresent:
        #        action.setEnabled(False)
        
    def deleteSelectedLabel(self):
        if self.ui.labelList.currentItem() is None:
            return
        try:
            shapes = self.itemToShapes[self.ui.labelList.currentItem()]
            for shape in shapes:
                del self.shapeToItem[shape]
                self.canvas.deleteShape(shape)
        except KeyError:
            self.ui.labelList.takeItem(self.ui.labelList.currentRow())
            return
            
        del self.itemToShapes[self.ui.labelList.currentItem()]
        self.ui.labelList.takeItem(self.ui.labelList.currentRow())
                 
        self.setDirty()

    def copyShape(self):
        self.canvas.endMove(copy=True)
        self.addShapeList(self.canvas.selectedShape)
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()

    def loadPredefinedClasses(self, predefClassesFile):
        label_data = open(predefClassesFile)
        data = json.load(label_data)
        label_configs = data["labels"]
        self.predefined_labels_num = len(label_configs)
        if self.predefined_labels_num > len(self.canvas.LABEL_COLORS) :
            QColor_list = self.canvas.random_colors((self.predefined_labels_num-len(self.canvas.LABEL_COLORS)))
            self.canvas.LABEL_COLORS.extend(QColor_list)
        idx = 0
        for config in label_configs:
            if config["enable"]:
                self.labelInfoDict[config["name"]] = (config["isPathClosed"], config["type"], self.canvas.LABEL_COLORS[idx])
                idx = idx + 1
            
        if len(self.labelInfoDict) > 0:
            self.ui.current_label.setText(list(self.labelInfoDict.keys())[0]);
        print("predefined labels:", self.labelInfoDict)

    def loadPascalXMLByFilename(self, xmlPath):
        if self.filePath is None:
            return
        if os.path.isfile(xmlPath) is False:
            return

        tVocParseReader = PascalVocReader(xmlPath)
        shapes = tVocParseReader.shapes
        self.loadLabels(shapes)
        self.canvas.verified = tVocParseReader.verified     
        