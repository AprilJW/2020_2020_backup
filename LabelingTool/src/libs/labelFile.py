# Copyright (c) 2016 Tzutalin
# Create by TzuTaLin <tzu.ta.lin@gmail.com>
from PyQt5.Qt import QByteArray
#from PyQt5.Qt import QCompass
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from base64 import b64encode, b64decode
from libs.pascal_voc_io import PascalVocWriter
from libs.pascal_voc_io import XML_EXT
import os.path
import sys
import time
import cv2
from numpy import sort
from libs.vizCompressed import vizCompressed

class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using XML ext
    # suffix = '.lif'
    suffix = XML_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False
        self.labels = []
        
    def setLabels(self, labels):
        self.labels = labels

    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image = QImage()
        image.load(imagePath)
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        self.writer = PascalVocWriter(imgFolderName, imgFileNameWithoutExt,
                                 imageShape, localImgPath=imagePath)
        self.writer.verified = self.verified

        for shape in shapes:
            label = shape['label']
            guid = shape['guid']
            parentGuid = shape['parentGuid']
            lineWidth = shape['lineWidth']
            points = shape['points']
            ellipse_points = shape['ellipse_points']
            rotate = shape['rotate']
            r1 = shape['r1']
            r2 = shape['r2']
            center = shape['center']
            #print("shape:", guid, " parent: ", parentGuid)
            self.writer.addVertexs(guid, parentGuid, label, lineWidth, rotate, r1, r2, center, points, ellipse_points)

        self.writer.save(targetFile=filename)
        return
    
    def saveData(self, filename, shapes, imagePath, cannyKSize, boxKSize, labelKSize, save_rf_Data = False):
        labelMat = self.writer.createLabelMat(imagePath, shapes, cannyKSize, boxKSize, labelKSize)
        image = QImage()
        image.load(imagePath)

        label = 0
        data = QByteArray()

        minMaxPoints = self.getMinMaxPoints(shapes)

        start = time.time()
        with open(filename, 'wb') as f:
            for y in range(image.height()):
                for x in range(image.width()):
                    if x > minMaxPoints[0] and y> minMaxPoints[1] and x < minMaxPoints[2] and y < minMaxPoints[3]:
                        label = labelMat[y, x]
                    else:
                        label = 0
                    data.append('{0}'.format(label))
                    #data.append('\n')
            
            #f.write(data)
            f.write(QtCore.qCompress(data, 9))
        
        elapse = time.time() - start
        if save_rf_Data:
            vizCompressed(filename)
        print("finish write data to file: {0}s".format(elapse))
        
    def getPixelLabel(self, x, y, shapes):
        labels = []
        if shapes is None:
            return 0
        for shape in shapes:
            result = shape.isContainsPixel(x, y)
            if result == 0:
                labels.append(self.labels.index((shape.label)) + 1)
        
        size = len(labels)
        if size < 1:
            return 0
        else:
            labels.sort()
            return labels[size-1] 

    def getMinMaxPoints(self, shapes):
        x = []
        y = []
        for shape in shapes:
            minMaxPoints = shape.getMinMaxPoints()
            x.append(minMaxPoints[0])
            x.append(minMaxPoints[2])
            y.append(minMaxPoints[1])
            y.append(minMaxPoints[3])
            
        x.sort()
        y.sort()
        
        size = len(x) 
        return (x[0], y[0], x[size-1], y[size-1])      
       
    def toggleVerify(self):
        self.verified = not self.verified

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix
