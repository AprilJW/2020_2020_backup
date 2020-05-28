#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
import json
import cv2
import numpy as np
from cv2 import bitwise_and
from PyQt5.Qt import QPointF
XML_EXT = '.xml'


class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False


    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True)
    
    def createLabelMat(self, imagePath, shapes, cannyKSize, boxKSize, labelKSize):
        print(imagePath, cannyKSize, boxKSize, labelKSize)
        srcImg = cv2.imread(imagePath)
        size = srcImg.shape[0], srcImg.shape[1]
        
        cannyImg = cv2.Canny(srcImg, 150, 200)
        kernel_canny = cv2.getStructuringElement(cv2.MORPH_RECT, cannyKSize)  #7 as param dilateCannyKSize
        dilatedCannyImg = cv2.dilate(cannyImg, kernel_canny)  
        
        kernel_box = cv2.getStructuringElement(cv2.MORPH_RECT, boxKSize) #20 as param dilateBoxKSize
        flags = np.zeros(size, dtype=np.uint8)
        labelMat = np.zeros(size, dtype=np.uint8)
        
        for shape in shapes:
            label = shape.label
            lineWidth = shape.lineWidth
            points = shape.points
            if label == 'box':
                polyMat = np.zeros(size, dtype=np.uint8)
                
                a3 = np.array([[[round(points[0].x()), round(points[0].y())], [round(points[1].x()), round(points[1].y())], [round(points[2].x()), round(points[2].y())], [round(points[3].x()), round(points[3].y())]]], dtype=np.int32)
                cv2.fillPoly(polyMat, a3, 255)
                
                dilatedPolyMat = cv2.dilate(polyMat, kernel_box)  
                
                flags += 10 * (dilatedPolyMat > 0).astype(flags.dtype)
            else:
                for n in range(len(points) - 1):
                    pixelValue = 0
                    if label == 'line':
                        pixelValue = 1
                    elif label == 'boundry':
                        pixelValue = 2  
                    cv2.line(labelMat, (round(points[n].x()), round(points[n].y())), (round(points[n + 1].x()), round(points[n + 1].y())), pixelValue, lineWidth)          

        label2Mask = bitwise_and(dilatedCannyImg, (flags > 10).astype(dilatedCannyImg.dtype))
        labelMat[label2Mask > 0] = 2
        
        kernel_labelMat = cv2.getStructuringElement(cv2.MORPH_RECT, labelKSize) #3 as param dilateLabelKSize
        dilatedLabelMat = cv2.dilate(labelMat, kernel_labelMat) 
        
        for shape in shapes:
            label = shape.label
            lineWidth = shape.lineWidth
            points = shape.points
            pixelValue = 0
            if label == 'eraser':
                for n in range(len(points) - 1):
                    cv2.line(dilatedLabelMat, (round(points[n].x()), round(points[n].y())), (round(points[n + 1].x()), round(points[n + 1].y())), pixelValue, lineWidth)          

        return dilatedLabelMat
                

    def genXML(self):
        """
            Return XML root 
        """
        # Check conditions
        if self.filename is None or \
                self.foldername is None or \
                self.imgSize is None:
            return None

        top = Element('annotation')
        top.set('verified', 'yes' if self.verified else 'no')

        folder = SubElement(top, 'folder')
        folder.text = self.foldername

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        localImgPath = SubElement(top, 'path')
        localImgPath.text = self.localImgPath

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top
        
    def addVertexs(self, guid, parentGuid, label, lineWidth, rotate, r1, r2, center, points, ellipse_points):
        if len(points) < 3:
            print("ignore shape that has less than 3 points")
            return
        bndbox = {}
        bndbox['guid'] = guid
        bndbox['parentGuid'] = parentGuid
        bndbox['name'] = label
        bndbox['lineWidth'] = lineWidth
        bndbox['rotate'] = rotate
        bndbox['points'] = points
        bndbox['ellipse_points'] = ellipse_points
        bndbox['r1'] = r1
        bndbox['r2'] = r2
        bndbox['center'] = center
        self.boxlist.append(bndbox)

    def appendObjects(self, top):
        for each_object in self.boxlist:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            try:
                name.text = each_object['name']
            except NameError:
                # Py3: NameError: name 'unicode' is not defined
                name.text = each_object['name']
                
            guid_item = SubElement(object_item, 'guid')
            guid_item.text = str(each_object['guid'])
            
            p_guid_item = SubElement(object_item, 'parentGuid')
            p_guid_item.text = str(each_object['parentGuid'])
                
            lineWidth = SubElement(object_item, 'lineWidth')
            lineWidth.text = str(int(each_object['lineWidth']))
            
            rotate = SubElement(object_item, 'rotate')
            rotate.text = str(int(each_object['rotate']))
            
            r1 = SubElement(object_item, 'r1')
            r1.text = str(int(each_object['r1']))
            
            r2 = SubElement(object_item, 'r2')
            r2.text = str(int(each_object['r2']))
            
            center_item = SubElement(object_item, 'center')
            center = each_object['center']
            x = SubElement(center_item, 'x')
            x.text = str(center[0])
            y = SubElement(center_item, 'y')
            y.text = str(center[1])
            
            points = each_object['points']
            for point in points:
                vertex = SubElement(object_item, 'vertex')
                x = SubElement(vertex, 'x')
                x.text = str(point[0])
                y = SubElement(vertex, 'y')
                y.text = str(point[1])
                
            ellipse_points = each_object['ellipse_points']
            for point in ellipse_points:
                ellipse_vertex = SubElement(object_item, 'ellipse_vertex')
                x = SubElement(ellipse_vertex, 'x')
                x.text = str(point[0])
                y = SubElement(ellipse_vertex, 'y')
                y.text = str(point[1])
            

    def save(self, targetFile=None):
        root = self.genXML()
        self.appendObjects(root)
        out_file = None
        if targetFile is None:
            out_file = codecs.open(
                self.filename + XML_EXT, 'w', encoding='utf-8')
        else:
            out_file = codecs.open(targetFile, 'w', encoding='utf-8')

        prettifyResult = self.prettify(root)
        out_file.write(prettifyResult.decode('utf8'))
        out_file.close()


class PascalVocReader:

    def __init__(self, filepath):
        # shapes type:
        # [label, lineWidth, rotate, r1, r2, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], ellipse_points]
        self.shapes = []
        self.filepath = filepath
        self.verified = False
        self.parseXML()

    def parseXML(self):
        self.shapes = []
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding='utf-8')
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        for object_iter in xmltree.findall('object'):
            points = []
            for vertex in object_iter.findall('vertex'):
                x = float(vertex.find('x').text)
                y = float(vertex.find('y').text)
                points.append((x, y))
                
            ellipse_points = []
            for vertex in object_iter.findall('ellipse_vertex'):
                x = float(vertex.find('x').text)
                y = float(vertex.find('y').text)
                ellipse_points.append((x, y))

            label = object_iter.find('name').text
            lineWidth = int(object_iter.find('lineWidth').text)
                
            rotate = 0
            try:
                rotate = int(object_iter.find('rotate').text)
            except AttributeError:
                rotate = 0
                
            r1 = 0.0
            r2 = 0.0
            try:
                r1 = float(object_iter.find('r1').text)
                r2 = float(object_iter.find('r2').text)
            except AttributeError:
                r1 = 0
                r2 = 0
            
            center_item = None
            center = QPointF(0, 0)
            try:
                center_item = object_iter.find('center')
            except AttributeError:
                center_item = None
            if center_item is not None:
                x = float(center_item.find('x').text)
                y = float(center_item.find('y').text)
                center = QPointF(x, y)
            self.shapes.append((label, lineWidth, points, ellipse_points, rotate, r1, r2, center))
        return True
