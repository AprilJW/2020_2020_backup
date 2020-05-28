#!/usr/bin/python
# -*- coding: utf-8 -*-
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import math
from math import sqrt, cos
import cv2
import numpy as np
import uuid

def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

DEFAULT_LINE_COLOR = QColor(255, 0, 0)
DEFAULT_SELECT_LINE_COLOR = QColor(0, 255, 0)

DEFAULT_VERTEX_FILL_COLOR = QColor(255, 0, 0)
DEFAULT_HVERTEX_FILL_COLOR = QColor(0, 255, 0)


class Shape(object):
    P_SQUARE, P_ROUND = range(2)
    S_POLYGON, S_Ellipse = list(range(2))

    MOVE_VERTEX, NEAR_VERTEX = range(2)
    
    OUTSIDE_SHAPE, INSIDE_SHAPE, IN_SHAPE_CONTOUR = range(3)
    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    
    point_type = P_ROUND
    point_size = 1
    scale = 1.0
    epsilon = 1

    def __init__(self, label= None):
        self.label = label
        self.points = []
        self.ellipse_points = []
        self.center = QPointF(0, 0)
        self.r1 = 0
        self.r2 = 0
        self.rotate = 0
        self.selected = False
        self.lineWidth = 1
        self.lineColor = DEFAULT_LINE_COLOR

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (1, self.P_ROUND),
            self.MOVE_VERTEX: (1, self.P_SQUARE),
        }
        self._closed = False
        self.isPathClosed = True
        self.d_type = self.S_POLYGON
        self.guid = QUuid.createUuid().toString()
        self.parentGuid = self.guid
       
    def close(self):
        self._closed = True
        if self.d_type == self.S_Ellipse:
            return self.fitEllipse()
        else:
            return True
        
    def clear(self):
        self.points.clear()
        
    def clear_ellipse(self):
        self.ellipse_points.clear()

    def addPoint(self, point):
        self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False
        
    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.lineColor
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(self.lineWidth, int(round(2.0 / self.scale))))
            painter.setPen(pen)
            
            #for ellipse, need store extra points in ellipse
            if self.d_type == self.S_Ellipse: 
                self.fitEllipse()
                self.sampleEllipsePoints()
            
            if self.d_type == self.S_POLYGON:       
                painter.drawPath(self.makeContainPath())
                
            #draw vertex
            vrtx_path = QPainterPath()
            for p in self.points:
                self.drawVertex(vrtx_path, p, self.point_size + 2)
            for p in self.ellipse_points:
                self.drawVertex(vrtx_path, p ,self.point_size)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.line_color)         
                               
    def paint_ellipse(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.lineColor
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(self.lineWidth, int(round(2.0 / self.scale))))
            painter.setPen(pen)
                     
            if self.d_type == self.S_Ellipse:
                painter.drawEllipse(QPointF(0, 0), self.r1, self.r2)         
                           
    def drawVertex(self, path, point, point_size):
        d = point_size / self.scale
        size, shape = self._highlightSettings[self._highlightMode]
        d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def containsPoint(self, point):  
        if len(self.points) <2:
            return self.OUTSIDE_SHAPE
                  
        if self.makeContainPath().contains(point):
            return self.INSIDE_SHAPE   #inside the shape
        return self.OUTSIDE_SHAPE #outside the shape
    
    def containsShape(self, shape):
        shape_points = shape.ellipse_points if shape.d_type == shape.S_Ellipse else shape.points
        return all(self.containsPoint(p) == self.INSIDE_SHAPE for p in shape_points)
    
    def containsNone(self, shapes):
        return all(not self.containsShape(shape) for shape in shapes)
    
    def intersectsWith(self, shape):
        self_points = self.ellipse_points if self.d_type == self.S_Ellipse else self.points
        shape_points = shape.ellipse_points if shape.d_type == shape.S_Ellipse else shape.points
        return (not self.containsShape(shape) and \
                any(self.containsPoint(p) == self.INSIDE_SHAPE for p in shape_points)) or \
                (not shape.containsShape(self) and \
                 any(shape.containsPoint(p) == shape.INSIDE_SHAPE for p in self_points))
    
    def makeContainPath(self):
        if self.d_type == self.S_POLYGON:
            path = QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
            path.lineTo(self.points[0])
            return path

        if self.d_type == self.S_Ellipse:
            path = QPainterPath(self.ellipse_points[0])
            for p in self.ellipse_points[1:]:
                path.lineTo(p)
            path.lineTo(self.ellipse_points[0])
            return path
    
    def fitEllipse(self):
        if len(self.points) < 6:
            if self._closed:
                self.points.clear()
                self.ellipse_points.clear()
            return False
        array = [[p.x(), p.y()] for p in self.points]
        contour = np.asarray(array, dtype=np.float32)
        (x,y), (h, l), self.rotate = cv2.fitEllipse(contour)
        self.center = QPointF(x, y)
        self.r1 = h / 2
        self.r2 = l / 2
        return True
        
    def sampleEllipsePoints(self):
        self.ellipse_points.clear()  
        for i in range(36):
            point = QPointF(self.r1 * math.cos((i + 1) * 10 * math.pi / 180),
                            self.r2 * math.sin((i + 1) * 10 * math.pi / 180))
            rotate = -self.rotate * math.pi / 180
            x = point.x() * math.cos(rotate) + point.y() * math.sin(rotate)
            y = -point.x() * math.sin(rotate) + point.y() * math.cos(rotate)
            point.setX(x)
            point.setY(y)
            point = point + self.center
            self.ellipse_points.append(point)
            
    def makeLinePath(self):
        path = QPainterPath()
        tmpPath = QPainterPath()
        if len(self.points) <2:
            return path
        
        length = len(self.points)
        for i in range(length-1):
            tmpPath = self.linePath(self.points[i], self.points[i+1])
            path.addPath(tmpPath)
        
        if self.isPathClosed and len(self.points) > 2:   
            tmpPath = self.linePath(self.points[length-1] , self.points[0])
            path.addPath(tmpPath)

        for point in self.points:
            path.addEllipse(point, self.lineWidth / 2, self.lineWidth / 2)
        
        for p in self.ellipse_points:
            path.lineTo(p)  
        
        return path
    
    def getMinMaxPoints(self):
        x = []
        y = []
        
        for point in self.points:
            x.append(point.x())
            y.append(point.y())
            
        x.sort()
        y.sort()
        
        size = len(self.points) 
        return (x[0], y[0], x[size-1], y[size-1])  
    
    def distance(self, p1, p2):
        sq1 = (p2.x() - p1.x())*(p2.x() - p1.x())
        sq2 = (p2.y() - p1.y())*(p2.y() - p1.y())
        return math.sqrt(sq1 + sq2)
    
    def isCloseEnough(self, p1, p2):
        return self.distance(p1, p2) < self.epsilon
    
    def linePath(self, p1, p2):
        path = QPainterPath()
        x1 = p1.x()
        y1 = p1.y()
        x2 = p2.x()
        y2 = p2.y()
        length = self.distance(p1, p2)
        if length < 1:
            return path
        halfWidth = self.lineWidth / 2
        deltaX = halfWidth * abs(y2-y1) / length
        deltaY = halfWidth * abs(x2-x1) / length
        
        if (x2-x1)*(y2-y1) < 0:
            deltaY = -deltaY
            
        point1 = QPointF((x1 -deltaX), (y1+deltaY))
        point2 = QPointF((x2 -deltaX), (y2+deltaY))
        point3 = QPointF((x2 +deltaX), (y2-deltaY))
        point4 = QPointF((x1 +deltaX), (y1-deltaY))
        
        path.moveTo(point1)
        path.lineTo(point2)
        path.lineTo(point3)
        path.lineTo(point4)
        path.lineTo(point1)
        
        return path      

    def boundingRect(self):
        return self.makeLinePath().boundingRect()  
    
    def isContainsPixel(self, x, y):
        return self.containsPoint(QPointF(x, y))

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.selected = self.selected
        shape._closed = self._closed
        shape.isPathClosed = self.isPathClosed
        shape.d_type = self.d_type
        shape.rotate = self.rotate
        shape.r1 = self.r1
        shape.r2 = self.r2
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
