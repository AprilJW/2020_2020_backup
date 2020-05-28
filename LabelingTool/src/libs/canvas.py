from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.shape import Shape
from libs.undo import AddPointCommand
from libs.undo import AddEraserCommand, AddCropCommand

from math import sqrt

import cv2, numpy as np
import random
import colorsys

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor
WAIT_CURSOR = Qt.WaitCursor

# class Canvas(QGLWidget):
isRound = True

def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

class Canvas(QWidget):
    POLYGON, Ellipse = list(range(2))
    
    LABEL_COLORS = [QColor(255, 255, 0), QColor(255, 0, 0), QColor(0, 255, 255),
                    QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 0, 255)]
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)
    changeLabel = pyqtSignal(object, str)

    CREATE, EDIT, ERASING = list(range(3))
    LABEL, CROP, MAGIC_WAND = list(range(3))
    
    epsilon = 2.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.current = None
        self.selectedShape = None
        self.selectedShapes = []  # save the selected shape here
        self.lineColor = QColor(255, 0, 0)
        self.line = Shape()
        self.lineWidth = 1
        self.prevPoint = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.hVertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menu = QMenu()
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.verified = False
        self.currentLabel = ""
        self.currentDType = self.POLYGON
        self.undoStack = QUndoStack(self)
        self.image_editing_status = self.LABEL
        self.eraser_strength = 5
        self.image_np = None
        self.erasing_points =[]

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShapes()

    def setEraserStrength(self, value=5):
        self.eraser_strength = value

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    def selectedVertex(self):
        return self.hVertex is not None

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transformPos(ev.pos())

        self.restoreCursor()

        if self.image_editing_status == Canvas.MAGIC_WAND and self.mode == self.ERASING:
            point = (int(pos.x()), int(pos.y()))
            if point[0] in range(self.image_np.shape[1]) and point[1] in range(self.image_np.shape[0]):
                self.erasing_points.append(point)

        # Polygon drawing.
        if self.drawing():
            self.overrideCursor(CURSOR_DRAW)
            if self.current:
                color = self.lineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)
                self.line[1] = pos
                self.line.line_color = color
                self.repaint()
                self.current.highlightClear()
            return
        
        # Polygon moving.
        if Qt.RightButton & ev.buttons():
            if self.selectedShape:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            return

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = index, shape
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos) > 0 :
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = None, shape
                self.setToolTip(
                    "Click & drag to move shape '%s'" % shape.label)
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape = None, None

    def show_numpy_image(self):
        img_rgb = cv2.cvtColor(self.image_np, cv2.COLOR_BGR2RGB)
        image = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], img_rgb.shape[1] * img_rgb.shape[2], QImage.Format_RGB888)
        self.loadPixmap(QPixmap.fromImage(image))

    def erasing(self, points):
        image_np_updated = self.image_np.copy()
        for point in points:
            image_np_copy = self.image_np.copy()
            cv2.floodFill(image_np_copy, None, seedPoint=point, newVal=(0,) * 3, loDiff=(self.eraser_strength,) * 3,
                          upDiff=(self.eraser_strength,) * 3)
            image_np_updated = cv2.bitwise_and(image_np_copy, image_np_updated)
        self.image_np = image_np_updated
        self.show_numpy_image()
        self.adjustSize()
        self.update()

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())
        if ev.button() == Qt.LeftButton:
            print('status', self.image_editing_status, 'mode ', self.mode)
            if self.image_editing_status == Canvas.MAGIC_WAND:
                self.mode = Canvas.ERASING
                point = (int(pos.x()), int(pos.y()))
                if point[0] in range(self.image_np.shape[1]) and point[1] in range(self.image_np.shape[0]):
                    self.erasing_points.append(point)
                    #cv2.circle(self.image_np, point, 5, (0,0,255), -1)

            elif self.drawing():
                self.setToolTip("drawing '%s'"% self.currentLabel)
                self.handleDrawing(pos)
            elif self.editing():
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()

            self.selectShapePoint(pos)
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            self.prevPoint = pos
            self.repaint()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.RightButton and self.drawing():
            self.finalise()
        elif ev.button() == Qt.LeftButton:
            if self.selectedShape:
                self.overrideCursor(CURSOR_GRAB)
            if self.image_editing_status == Canvas.MAGIC_WAND:
                self.undoStack.push(AddEraserCommand(self))
                self.setEditing(True)
                self.erasing_points.clear()


    def endMove(self, copy=False):
        assert self.selectedShape
        #del shape.fill_color
        #del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            self.selectedShape.points = [p for p in shape.points]

    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()

    def handleDrawing(self, pos):
        if self.current:
            self.undoStack.push(AddPointCommand(self, pos))
            self.line.points = [pos, pos]
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.label = self.currentLabel
            self.current.d_type = self.currentDType
            self.undoStack.push(AddPointCommand(self, pos))
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.           
        pos = self.transformPos(ev.pos())
        if ev.button() == Qt.LeftButton:

            self.restoreCursor()
            shape = self.getShapeFromPoint(pos)
            if shape is None:
                return

            result = False
            lineWidth, result = QInputDialog.getInt(self, "Set LineWidth for Shape", "Line Width",
                                                   shape.lineWidth, 0, 100, 1)
            if not result:
                return

            shape.lineWidth = lineWidth #update with new linewidth
            shape.paint(self._painter)
        elif ev.button() == Qt.RightButton:
            self.restoreCursor()
            shape = self.getShapeFromPoint(pos)
            if shape is None:
                return
            result = False
            changed_label, result = QInputDialog.getText(self, "Change Label for Shape", "Change Label",
                                                         QLineEdit.Normal, shape.label)
            if not result:
                return
            self.changeLabel.emit(shape, changed_label)
            shape.paint(self._painter)

            
    def getShapeFromPoint(self, p):
        for shape in self.shapes:
            if shape.containsPoint(p) > 0 :
                return shape

    def selectShapes(self, shapes, label, labelInfo):
        self.deSelectShapes()
        if shapes is None:
            return
        for shape in shapes:
            shape.selected = True
            if label is not None:
                shape.label = label
            if labelInfo is not None:
                shape.isPathClosed = labelInfo[0]
                shape.d_type = labelInfo[1]
            self.selectedShapes.append(shape)
            self.selectedShape = shape
        
        self.setHiding()    
        self.selectionChanged.emit(True)
        self.update()

    def selectShapePoint(self, point):
        self.deSelectShapes()
        """Select the first shape created which contains this point."""
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            return
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point) > 0:
                shape.selected = True
                self.selectedShape = shape
                self.selectedShapes.append(shape)
                self.calculateOffsets(shape, point)
                self.setHiding()
                self.selectionChanged.emit(True)
                return
        
        self.deSelectShapes()#if not shape is selected, deselect all shapes

    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)

        shiftPos = pos - point
        shape.moveVertexBy(index, shiftPos)

    def boundedMoveShape(self, shape, pos):
        if self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    def deSelectShapes(self):
        for shape in self.shapes:
            shape.selected = False
        
        self.setHiding(False)    
        self.selectedShapes.clear()
        self.selectedShape = None
        self.selectionChanged.emit(False)
        self.update()

    def deleteSelected(self):
        if self.selectedShape:
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()
            return shape
        
    def deleteShape(self, shape):
        self.shapes.remove(shape)
        self.update()

    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShapes()
            self.shapes.append(shape)
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            return shape

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())
        
        p.drawPixmap(0, 0, self.pixmap)
        
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape  
                shape.paint(p) #paint points without transform
                p.save()
                p.translate(shape.center)
                p.rotate(shape.rotate)
                shape.paint_ellipse(p)
                p.restore()
        if self.current:
            self.current.paint(p)
            self.line.paint(p)

        #self.setAutoFillBackground(True)
        p.end()

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

    def image_crop(self, reverse):
        xmin = int(self.image_np.shape[1])
        ymin = int(self.image_np.shape[0])
        xmax = 0
        ymax = 0

        # print('image crop image np', self.image_np)
        alpha = np.zeros((self.image_np.shape[0], self.image_np.shape[1], 1), np.uint8)
        if reverse:
            color = 0
            alpha.fill(255)
        else:
            color = 255
        # print('shapes', self.shapes)
        for shape in self.shapes:
            cnt = []
            for point in shape.points:
                x = int(point.x())
                y = int(point.y())
                cnt.append([[x, y]])
                xmin = min(xmin, x)
                ymin = min(ymin, y)
                xmax = max(xmax, x)
                ymax = max(ymax, y)
            if len(cnt) > 0:
                cv2.drawContours(alpha, [np.array(cnt).astype(np.int32)], 0, color, cv2.FILLED)
        self.image_np = cv2.bitwise_and(self.image_np, self.image_np, mask=alpha)
        if not reverse:
            self.cropImageNp([int(xmin), int(ymin), int(xmax), int(ymax)])
        self.show_numpy_image()

    def finalise(self):
        if self.current is None:
            return
        if self.current.close():
            self.shapes.append(self.current)
            self.current = None
            self.setHiding(False)
            self.drawingPolygon.emit(False)
            self.newShape.emit()
            self.update()
        else:
            self.current = None
            self.setHiding(False)
            self.update()

    def cropping(self, reverse=False):
        self.undoStack.push(AddCropCommand(self, reverse))

    def closeEnough(self, p1, p2):
        #d = distance(p1 - p2)
        #m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QPointF(min(max(0, x2), max(x3, x4)), y3)
        return QPointF(x, y)

    def intersectingEdges(self, x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                yield d, i, (x, y)

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape and self.current:
            print('ESC press')
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Left and self.selectedShape:
            self.moveOnePixel('Left')
        elif key == Qt.Key_Right and self.selectedShape:
            self.moveOnePixel('Right')
        elif key == Qt.Key_Up and self.selectedShape:
            self.moveOnePixel('Up')
        elif key == Qt.Key_Down and self.selectedShape:
            self.moveOnePixel('Down')

    def moveOnePixel(self, direction):
        # print(self.selectedShape.points)
        if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selectedShape.points[0] += QPointF(-1.0, 0)
            self.selectedShape.points[1] += QPointF(-1.0, 0)
            self.selectedShape.points[2] += QPointF(-1.0, 0)
            self.selectedShape.points[3] += QPointF(-1.0, 0)
        elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selectedShape.points[0] += QPointF(1.0, 0)
            self.selectedShape.points[1] += QPointF(1.0, 0)
            self.selectedShape.points[2] += QPointF(1.0, 0)
            self.selectedShape.points[3] += QPointF(1.0, 0)
        elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selectedShape.points[0] += QPointF(0, -1.0)
            self.selectedShape.points[1] += QPointF(0, -1.0)
            self.selectedShape.points[2] += QPointF(0, -1.0)
            self.selectedShape.points[3] += QPointF(0, -1.0)
        elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selectedShape.points[0] += QPointF(0, 1.0)
            self.selectedShape.points[1] += QPointF(0, 1.0)
            self.selectedShape.points[2] += QPointF(0, 1.0)
            self.selectedShape.points[3] += QPointF(0, 1.0)
        self.shapeMoved.emit()
        self.repaint()

    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)

    def setLastLabel(self, text):
        assert text
        self.shapes[-1].label = text
        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.current.popPoint()
        self.line.points = [self.current[-1], self.current[0]]
        if self.current.d_type == self.Ellipse:
            self.current.clear_ellipse()
        self.drawingPolygon.emit(True)

    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
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
        
    def updateShapes(self, lineWidth):
        for shape in self.shapes:
            shape.linewidth = lineWidth
            shape.paint(self._painter)
            
    def isShapeHasChildren(self, selected_shape):
        return any(shape.parentGuid == selected_shape.guid for shape in self.shapes)
        
    def cropImageNp(self, bbox):
        self.image_np = self.image_np[bbox[1]:bbox[3], bbox[0]:bbox[2]]        
    
    def random_colors(self, N):
         """
         Generate random colors.
         To get visually distinct colors, generate them in HSV space then
         convert to RGB.
         """
         n = np.random.random()
         hsv = [(n, 1-n, 0.4) for i in range(N)]
         color_list = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
         QColor_list = []
         for i in color_list :
             QColor_list.append(QColor(i[0]*255, i[1]*255, i[2]*255))                       
         random.shuffle(QColor_list)
         return QColor_list