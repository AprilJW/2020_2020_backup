from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from math import sqrt
import cv2
import numpy as np
import json
import colorsys
import random
import logging

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor
WAIT_CURSOR = Qt.WaitCursor

PIXEL_POS   = "pos"
PIXEL_RATIO = "ratio"
PIXEL_GRAY_VALUE = "gray_value"
PIXEL_RGB_VALUE   = "rgb_value"

PIL_IMAGE_MODE_RGB = 'RGB'

PIL_IMAGE_IN_8BIT = {'P', 'L'}
PIL_IMAGE_IN_24BIT = {'RGB', 'RGBA'}

def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

class Canvas(QWidget):
    scrollRequest = pyqtSignal(int, int)
    rgbValueGot = pyqtSignal(int, int, int)
    roiSelected = pyqtSignal(QRect)
    
    epsilon = 1.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        self.setMinimumHeight(1000)
        self.setMinimumWidth(1000)
        self.pixmap = QPixmap()
        self.mask_path = ''
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        self.scale = 1.0
        # Menus:
        self.menu = QMenu()
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.pil_img = None
        self.enable_drawing_roi = False
        self.pos_mouse_press = None
        self.pos_mouse_release = None
        
        self.image_mode = PIL_IMAGE_MODE_RGB
        self.image_shape = None
        self.pixel_infos = {}
        #for mask image
        self.pixelValue = 0
        self.valueToPixels = {} # num : pixels
        self.pixelValueToState = {} # pixelValue: (selected, rgb_value)
        self.total_pixel_count = 0
        self.pixel_ratio = {} # pixelValue : ratio
        self.vertex_infos = []
        self.label_name_to_color = {} #name:color
        self.cumu_labels_list = []

    def format_tool_tip(self, pos):
        tooltip = ""
        tooltip += 'w:'+ str(self.image_shape[0]) + ' h:' + str(self.image_shape[1]) + '\n'
        for info in self.pixel_infos.keys():
            value = ":{0} ".format(self.pixel_infos[info])
            tooltip += info + value + '\n'
        tooltip += 'label:' + str(self.get_label_info(pos)) + '\n'
        self.setToolTip(tooltip)      

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transformPos(ev.pos())
        if self.pos_mouse_press is not None:
            self.pos_mouse_release = pos
        try:
            self.pixel_infos[PIXEL_POS] = (pos.x(), pos.y())
            if self.image_mode in PIL_IMAGE_IN_24BIT:
                self.pixel_infos[PIXEL_RGB_VALUE] = self.pil_img.getpixel((pos.x(), pos.y()))
            elif self.image_mode in PIL_IMAGE_IN_8BIT:
                self.pixel_infos[PIXEL_RATIO] = self.pixel_ratio[self.pixels[pos.x(), pos.y()]]
                self.pixel_infos[PIXEL_GRAY_VALUE] = self.pil_img.getpixel((pos.x(), pos.y()))
                self.pixel_infos[PIXEL_RGB_VALUE] = self.pixelValueToState[self.pixel_infos[PIXEL_GRAY_VALUE]][1]

            self.format_tool_tip(pos)
        except AttributeError:
            pass
        except IndexError:
            pass
        
        self.restoreCursor()
        self.update()

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())
        self.pos_mouse_press = pos
        if self.pil_img is None:
            return
        
        width, height = self.pil_img.size
        if pos.x() < width and pos.y() < height:
            self.pixelValue = self.pil_img.getpixel((pos.x(), pos.y())) #0~128
        if self.image_mode == PIL_IMAGE_MODE_RGB:
            self.rgbValueGot.emit(*self.pixelValue)
        if self.image_mode in PIL_IMAGE_IN_8BIT:
            self.setPixelValueHighlight(self.pixelValue)

    def mouseReleaseEvent(self, ev):
        pos = self.transformPos(ev.pos())
        self.pos_mouse_release = pos
        self.roiSelected.emit(self.calc_roi())
        self.reset_roi()
        self.update()
        
    def endMove(self, copy=False):
        pass
    
    def mouseDoubleClickEvent(self, ev):
        pos = self.transformPos(ev.pos())
        pixelValue = self.pixels[pos.x(), pos.y()]
        newPixelValue, result = QInputDialog.getInt(self, "Set New Pixel Value for selected pixels", "Pixel Value",
                                               1, 0, 100, 1)
        if pixelValue == newPixelValue:
            return
        
        pixels = self.valueToPixels[pixelValue]
        for x, y in pixels:
            self.pil_img.putpixel((x, y), newPixelValue)
            
        self.setImage(self.pil_img)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)
        
        if self.pil_img is None:
            return

        p = self._painter
        p.begin(self)

        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)

        for pixelValue in self.valueToPixels.keys():
            state = self.pixelValueToState[pixelValue]
            r, g, b = state[1]
            color = QColor(r, g, b) if not state[0] else QColor(255, 255, 0)
            self.drawPoints(p, self.valueToPixels[pixelValue], color)

        self.draw_label_infos(p, self.vertex_infos)
        
        if self.enable_drawing_roi:
            self.drawRoi(p)

        if self.mask_path:
            mask_img = cv2.imread(self.mask_path)
            points_array = np.where(mask_img > 0)
            points = zip(points_array[1], points_array[0])
            for x, y in points:
                # 2,1,0 represent the g,b,r channel
                p.setPen(QColor(mask_img[y, x, 2], mask_img[y, x, 1], mask_img[y, x, 0]))
                p.drawPoint(x, y)

        p.end()

    def drawRoi(self, painter):
        painter.setPen(QColor(0, 255, 0))
        roi = self.calc_roi()
        if roi is not None:
            painter.drawRect(roi)
        
    def drawPoints(self, painter, pixels, color):
        for w, h in pixels:
            painter.setPen(color)
            painter.drawPoint(w, h)
            
    def drawPolygon(self, painter, label, points):
        self.update_labels_names_to_colors()
        poly_points = []
        for point in points:
            poly_points.append(QPointF(float(point[0]), float(point[1])))
        if label in self.label_name_to_color:
            painter.setPen(self.label_name_to_color[label])
            painter.setBrush(self.label_name_to_color[label])

        else:
            logging.critical("in canvas.py function setLabels gives the error: Label not in label_name_to_color")
            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(QColor(255, 0, 0))
        painter.drawPolygon(*poly_points)

    def draw_label_infos(self, painter, vertex_infos):
        for vertex_info in vertex_infos:
            if "parent_id" in vertex_info[0] :
                info_label = vertex_info[0].split("\n")[0] #only json file contain parent_id, xml file not contain parent_id
            else:
                info_label = vertex_info[0]
            if not info_label in self.cumu_labels_list :
                self.accumulate_PrevImg_labels_num = len(self.cumu_labels_list)
                self.cumu_labels_list.append(info_label)
                self.accumulate_NextImg_labels_num = len(self.cumu_labels_list)
            self.drawPolygon(painter, info_label, vertex_info[1])

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)
    
    def setPixelValueHighlight(self, pixelValue):
        self.pixelValue = pixelValue
        if self.image_mode not in PIL_IMAGE_IN_8BIT:
            return
        for value in self.pixelValueToState.keys():
            state = self.pixelValueToState[value]
            self.pixelValueToState[value] = (False, state[1])
            if self.pixelValue > 0:
                state = self.pixelValueToState[self.value]
                self.pixelValueToState[self.pixelValue] = (True, state[1])
        self.repaint()

    def setImage(self, img, calc_pixel_value):
        self.image_shape = img.size
        self.pil_img = img
        self.image_mode = img.mode
        if (self.pil_img.mode in PIL_IMAGE_IN_8BIT) and calc_pixel_value:
            self.calcPixelInfo()

    def update_labels_names_to_colors(self):
        if self.accumulate_PrevImg_labels_num == self.accumulate_NextImg_labels_num :
            return self.label_name_to_color
        else:
            for i in range(self.accumulate_NextImg_labels_num - self.accumulate_PrevImg_labels_num):
                append_label = self.cumu_labels_list[-(i + 1)]
                if not append_label in self.label_name_to_color.keys():
                    self.label_name_to_color[append_label] = self.random_color()

    def random_color(self, bright=True):
        """
        Generate random colors.
        To get visually distinct colors, generate them in HSV space then
        convert to RGB.
        """
        brightness = 1.0 if bright else 0.7
        N = random.random()
        hsv = (N , 1, brightness)
        color_list = list(colorsys.hsv_to_rgb(hsv[0], hsv[1],hsv[2])) #list(map(lambda c: colorsys.hsv_to_rgb(), hsv))
        random_QColor = QColor(color_list[0] * 255, color_list[1] * 255, color_list[2] * 255, 150)
        return random_QColor

    def clearPixelInfo(self):
        self.valueToPixels.clear()
        self.pixel_ratio.clear()
        self.pixelValueToState.clear()
        self.pixel_infos.clear()
        
    def calcPixelInfo(self):
        self.pixels = self.pil_img.load()
        width, height = self.pil_img.size
        self.total_pixel_count = width * height
        
        self.clearPixelInfo()
        
        rgb_img = self.pil_img.convert(PIL_IMAGE_MODE_RGB)
        
        for w in range(width):
            for h in range(height):
                value = self.pixels[w, h]
                try:
                    self.valueToPixels[value].append((w,h))
                except KeyError:
                    self.valueToPixels[value] = []
                    self.valueToPixels[value].append((w,h))
                
                self.pixelValueToState[value] = (False, rgb_img.getpixel((w, h)))
                
        for pixelValue in self.valueToPixels.keys():
            self.pixel_ratio[pixelValue] = len(self.valueToPixels[pixelValue]) / (self.total_pixel_count)
        print("map:", self.pixelValueToState, self.pixel_ratio)
        
    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        delta = ev.angleDelta()
        h_delta = delta.x()
        v_delta = delta.y()
        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.scale += 0.01 * v_delta / (8 * 15)
            self.adjustSize()
            self.update()
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)

    def loadPixmap(self, pixmap, vertex_infos = []):
        self.pixmap = pixmap
        self.vertex_infos = vertex_infos
        self.repaint()

    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.update()

    def get_label_info(self, pos):
        labels = []
        contour_areas = []
        for vertex_info in self.vertex_infos:
            if cv2.pointPolygonTest(np.array(vertex_info[1]).astype(int), (pos.x(), pos.y()), False) == 1:
                contour_areas.append(cv2.contourArea(np.array(vertex_info[1]).astype(int)))
                labels.append(vertex_info[0])
        if contour_areas:
            return labels[contour_areas.index(min(contour_areas))]
        else:
            return 'None'
    
    def calc_roi(self):
        if self.pos_mouse_press is None or self.pos_mouse_release is None:
            return None
        return QRect(self.pos_mouse_press.toPoint(), self.pos_mouse_release.toPoint())
        
    def reset_roi(self):
        self.pos_mouse_press = self.pos_mouse_release = None
