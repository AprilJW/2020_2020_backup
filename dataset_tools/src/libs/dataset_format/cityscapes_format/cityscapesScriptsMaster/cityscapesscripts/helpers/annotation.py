#!/usr/bin/python
#
# Classes to store, read, and write annotations
#

import os
import json
from collections import namedtuple
  
# get current date and time
import datetime
import locale

# A point in a polygon
Point = namedtuple('Point', ['x', 'y'])
Hierachy = namedtuple('Hierarchy', ['next', 'previous', 'child', 'parent'])

# Class that contains the information of a single annotated object
class CsObject:
    # Constructor
    def __init__(self):
        # the label
        self.label    = ""
        # the polygon as list of points
        self.polygon  = []

        # the object ID
        self.id       = -1
        # If deleted or not
        self.deleted  = 0
        # If verified or not
        self.verified = 0
        # The date string
        self.date     = ""
        # The username
        self.user     = ""
        # Draw the object
        # Not read from or written to JSON
        # Set to False if deleted object
        # Might be set to False by the application for other reasons
        self.draw     = True

    def __str__(self):
        polyText = ""
        if len(self.polygon) > 0:
            if (type(self.polygon[0]) is dict):
                polyText += '[ {"hierarchy": ['
                for h in self.polygon[0]["hierarchy"]:
                    polyText += '[{},{},{},{}] '.format(h.next, h.previous, h.child, h.parent)
                polyText += '], "contours": ['
                for group in self.polygon[0]["contours"]:
                    polyText += '['
                    for points in group:
                        if len(points) <= 4:
                            for p in points:
                                polyText += '({},{}) '.format(p.x, p.y)
                        else:
                            polyText += '({},{}) ({},{}) ... ({},{}) ({},{})'.format(
                                points[0].x, points[0].y,
                                points[1].x, points[1].y,
                                points[-2].x, points[-2].y,
                                points[-1].x, points[-1].y)
                    polyText += '], '

                polyText = polyText[:-2]
                polyText += ']}]'

            else:
                for group in self.polygon:
                    if len(group) <= 4:
                        for p in group:
                            polyText += '({},{}) '.format( p.x , p.y )
                    else:
                        polyText += '({},{}) ({},{}) ... ({},{}) ({},{})'.format(
                            group[ 0].x , group[ 0].y ,
                            group[ 1].x , group[ 1].y ,
                            group[-2].x , group[-2].y ,
                            group[-1].x , group[-1].y )
        else:
            polyText = "none"
        text = "Object: [{} : {}]".format( self.label , polyText )
        return text

    def fromJsonText(self, jsonText, objId):
        self.id = objId
        self.label = str(jsonText['label'])
        if(type(jsonText['polygon'][0]) is dict):
            self.polygon.append({"hierarchy":[], "contours":[]})
            hier = jsonText['polygon'][0]['hierarchy'][0]
            for h in hier:
                self.polygon[0]['hierarchy'].append(Hierachy(h[0],h[1],h[2],h[3]))
            contours = jsonText['polygon'][0]['contours']
            for contour in contours:
                group = []
                for p in contour:
                    group.append(Point(p[0], p[1]))
                self.polygon[0]['contours'].append(group)
        else:
            for p in jsonText['polygon']:
                self.polygon.append(Point(p[0],p[1]))

        if 'deleted' in jsonText.keys():
            self.deleted = jsonText['deleted']
        else:
            self.deleted = 0
        if 'verified' in jsonText.keys():
            self.verified = jsonText['verified']
        else:
            self.verified = 1
        if 'user' in jsonText.keys():
            self.user = jsonText['user']
        else:
            self.user = ''
        if 'date' in jsonText.keys():
            self.date = jsonText['date']
        else:
            self.date = ''

        if self.deleted == 1:
            self.draw = False
        else:
            self.draw = True

    def toJsonText(self):
        objDict = {}
        objDict['label'] = self.label
        objDict['id'] = self.id
        objDict['deleted'] = self.deleted
        objDict['verified'] = self.verified
        objDict['user'] = self.user
        objDict['date'] = self.date
        objDict['polygon'] = []
        if(len(self.polygon) > 0 and type(self.polygon[0]) is dict):
            objDict['polygon'].append({"hierarchy":[], "contours":[]})
            hierarchy = []
            for h in self.polygon[0]["hierarchy"]:
                hierarchy.append([h.next, h.previous, h.child, h.parent])
            objDict['polygon'][0]["hierarchy"] = hierarchy
            contours = []
            for group in self.polygon:
                contour = []
                for pt in group:
                    contour.append([pt.x, pt.y])
                contours.append(contour)
            objDict['polygon'][0]["contours"] = contours
        else:
            for pt in self.polygon:
                objDict['polygon'].append([pt.x, pt.y])
        return objDict

    def updateDate( self ):
        try:
            locale.setlocale( locale.LC_ALL , 'en_US' )
        except locale.Error:
            locale.setlocale( locale.LC_ALL , 'us_us' )
        except:
            pass
        self.date = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")

    # Mark the object as deleted
    def delete(self):
        self.deleted = 1
        self.draw    = False

# The annotation of a whole image
class Annotation:
    # Constructor
    def __init__(self):
        # the width of that image and thus of the label image
        self.imgWidth  = 0
        # the height of that image and thus of the label image
        self.imgHeight = 0
        # the list of objects
        self.objects = []

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def fromJsonText(self, jsonText):
        jsonDict = json.loads(jsonText)
        self.imgWidth  = int(jsonDict['imgWidth'])
        self.imgHeight = int(jsonDict['imgHeight'])
        self.objects   = []
        for objId, objIn in enumerate(jsonDict[ 'objects' ]):
            obj = CsObject()
            obj.fromJsonText(objIn, objId)
            self.objects.append(obj)

    def toJsonText(self):
        jsonDict = {}
        jsonDict['imgWidth'] = self.imgWidth
        jsonDict['imgHeight'] = self.imgHeight
        jsonDict['objects'] = []
        for obj in self.objects:
            objDict = obj.toJsonDict()
            jsonDict['objects'].append(objDict)
  
        return jsonDict

    # Read a json formatted polygon file and return the annotation
    def fromJsonFile(self, jsonFile):
        if not os.path.isfile(jsonFile):
            print('Given json file not found: {}'.format(jsonFile))
            return
        with open(jsonFile, 'r') as f:
            jsonText = f.read()
            self.fromJsonText(jsonText)

    def toJsonFile(self, jsonFile):
        with open(jsonFile, 'w') as f:
            f.write(self.toJson())
            

# a dummy example
if __name__ == "__main__":
    obj = CsObject()
    obj.label = 'car'
    group = []
    group.append( Point( 0 , 0 ) )
    group.append( Point( 1 , 0 ) )
    group.append( Point( 1 , 1 ) )
    group.append( Point( 0 , 1 ) )
    obj.polygon.append(group)

    obj_hier = CsObject()
    obj_hier.label = 'metal'

    metal_polygon = {}
    group = []
    group.append(Hierachy(0,0,0,0))
    group.append(Hierachy(-1,-1,-1,-1))
    group.append(Hierachy(1,1,1,1))
    metal_polygon["hierarchy"] = group
    contours = []
    group = []
    group.append(Point(0, 0))
    group.append(Point(1, 0))
    group.append(Point(1, 1))
    group.append(Point(0, 1))
    contours.append(group)

    group = []
    group.append(Point(0, 0))
    group.append(Point(1, 0))
    group.append(Point(1, 1))
    group.append(Point(0, 1))
    contours.append(group)
    metal_polygon["contours"] = contours
    obj_hier.polygon.append(metal_polygon)
    print(metal_polygon)
    print(obj)
    print(obj_hier)