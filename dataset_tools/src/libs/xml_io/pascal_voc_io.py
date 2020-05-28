#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
import json
import uuid
import logging

XML_EXT = '.xml'
ENCODE_METHOD = 'utf-8'

def addNode(obj_dict, key, parent_node, tag):
    try:
        text = str(obj_dict[key])
        node = SubElement(parent_node, tag)
        node.text = text
    except NameError:
        logging.debug("key not exist:" + key)
        pass

class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize,databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.bndbox_list = []
        self.vertexs_list = []
        self.localImgPath = localImgPath
        self.verified = False


    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True, encoding=ENCODE_METHOD).replace("  ".encode(), "\t".encode())

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
        #print("size:", self.imgSize)
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])

        depth.text = str(self.imgSize[2]) if len(self.imgSize) == 3 else '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top
        
    def addVertexs(self, label, lineWidth, points, guid, parentGuid):     
        bndbox = {}
        bndbox['guid'] = guid
        bndbox['parentGuid'] = parentGuid
        bndbox['name'] = label
        bndbox['lineWidth'] = lineWidth
        bndbox['points'] = points
        self.vertexs_list.append(bndbox)
        
    def addBndBox(self, xmin, ymin, xmax, ymax, cx=0,cy=0,w=0,h=0,theta=0,name="",difficult = 0):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax,'cx':cx,'cy':cy,'w':w,'h':h,'theta':theta}
        bndbox['name'] = name
        self.bndbox_list.append(bndbox)
        
    def appendObjects(self, top):
        for each_object in self.vertexs_list:
            object_item = SubElement(top, 'object')
            addNode(each_object, 'name', object_item, 'name')
            addNode(each_object, 'guid', object_item, 'guid')
            addNode(each_object, 'parentGuid', object_item, 'parentGuid')
            addNode(each_object, 'lineWidth', object_item, 'lineWidth')
      
            points = each_object['points']
            for point in points:
                vertex = SubElement(object_item, 'vertex')
                x = SubElement(vertex, 'x')
                x.text = str(point[0])
                y = SubElement(vertex, 'y')
                y.text = str(point[1])
           
        for each_object in self.bndbox_list:
            object_item = SubElement(top, 'object')
            addNode(each_object, 'name', object_item, 'name')
            bndbox_item = SubElement(object_item, 'bndbox')
            addNode(each_object, 'xmin', bndbox_item, 'xmin')
            addNode(each_object, 'ymin', bndbox_item, 'ymin')
            addNode(each_object, 'xmax', bndbox_item, 'xmax')
            addNode(each_object, 'ymax', bndbox_item, 'ymax')
            
            rotbox_item = SubElement(object_item,'rotbox')
            addNode(each_object, 'cx', rotbox_item, 'cx')
            addNode(each_object, 'cy', rotbox_item, 'cy')
            addNode(each_object, 'w', rotbox_item, 'w')
            addNode(each_object, 'h', rotbox_item, 'h')
            addNode(each_object, 'theta', rotbox_item, 'theta')
                
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
        # [label, lineWidth, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]]
        self.shapes = []
        self.roi = []
        self.bndboxs = []
        self.rotboxs = []
        self.filepath = filepath
        self.verified = False
        self.parseXML()

    def getShapes(self):
        return self.shapes

    def getBndboxs(self):
        return self.bndboxs

    def getROI(self):
        return self.roi

    def addShapeWithVertex(self, label, lineWidth, points, guid, parentGuid):
        self.shapes.append((label, lineWidth, points, guid, parentGuid))

    def addShapeWithBndbox(self, label, bndbox):
        if bndbox is None:
            return
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        if label != 'ROI':
            self.bndboxs.append((xmin, ymin, xmax, ymax, label))
        else:
            self.roi = [xmin, ymin, xmax, ymax]
            
    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding='utf-8')
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        
        for object_iter in xmltree.findall('size'):
            self.imgWidth = object_iter.find('width').text
            self.imgHeight = object_iter.find('height').text

        for object_iter in xmltree.findall('object'):
            self.parseShapeVertex(object_iter)
            self.parseShapeBndbox(object_iter)
        
    def parseShapeVertex(self, object_iter):
        points = []
        vertices = object_iter.findall('vertex')
        ellipse_vertices = object_iter.findall('ellipse_vertex')
        if ellipse_vertices:
            for ellipse_vertex in ellipse_vertices:
                x = int(float(ellipse_vertex.find('x').text))
                y = int(float(ellipse_vertex.find('y').text))
                points.append((x, y))
        else:
            for vertex in vertices:
                x = int(float(vertex.find('x').text))
                y = int(float(vertex.find('y').text))
                points.append((x, y))

        label = object_iter.find('name').text
        lineWidth = 2
        if object_iter.find('lineWidth') is not None:
            lineWidth = int(object_iter.find('lineWidth').text)
           
        guid = uuid.uuid4()
        parentGuid = guid
        if object_iter.find('guid') is not None:
            guid = object_iter.find('guid').text
            parentGuid = object_iter.find('parentGuid').text
            
        self.addShapeWithVertex(label, lineWidth, points, guid, parentGuid)
    
    def parseShapeBndbox(self, object_iter):
        bndbox = object_iter.find("bndbox")
        rotbox = object_iter.find("rotbox")
        label = object_iter.find('name').text
        self.addShapeWithBndbox(label, bndbox) 
