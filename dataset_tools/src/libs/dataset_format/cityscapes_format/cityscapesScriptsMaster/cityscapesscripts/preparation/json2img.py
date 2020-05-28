#!/usr/bin/python
#
# Reads labels as polygons in JSON format and converts them to label images,
# where each pixel has an ID that represents the ground truth label.
#
# Usage: json2labelImg.py [OPTIONS] <input json> <output image>
# Options:
#   -h   print a little help text
#   -t   use train IDs
#
# Can also be used by including as a module.
#
# Uses the mapping defined in 'labels.py'.
#
# See also createTrainIdLabelImgs.py to apply the mapping to all annotations in Cityscapes.
#

# python imports
import os, sys, getopt
import numpy as np
import cv2
from PIL import Image

import time
# cityscapes imports
sys.path.append( os.path.normpath( os.path.join( os.path.dirname( __file__ ) , '..' , 'helpers' ) ) )
from annotation import Annotation
from labels     import labels, name2label

# Print the information
def printHelp():
    print('{} [OPTIONS] inputJson outputImg'.format(os.path.basename(sys.argv[0])))
    print('')
    print('Reads labels as polygons in JSON format and converts them to label images,')
    print('where each pixel has an ID that represents the ground truth label.')
    print('')
    print('Options:')
    print(' -h                 Print this help')
    print(' -t                 Use the "trainIDs" instead of the regular mapping. See "labels.py" for details.')
    print(' -c                 Use the "color" instead of the regular mapping. See "labels.py" for details.')

# Print an error message and quit
def printError(message):
    print('ERROR: {}'.format(message))
    print('')
    print('USAGE:')
    printHelp()
    sys.exit(-1)

# Convert the given annotation to a label image
def createLabelImage(annotation, encoding, outline=None):
    # the background
    if encoding == "ids" or encoding == 'instance' or encoding == "color" or encoding == "label":
        background = name2label['unlabeled'].id
    elif encoding == "trainIds":
        background = name2label['unlabeled'].trainId
    else:
        print("Unknown encoding '{}'".format(encoding))
        return None

    # Create a black image
    # this is the image that we want to create
    if encoding == "color":
        imgProto = np.full(( annotation.imgHeight, annotation.imgWidth, 3), background, np.uint8)
    elif encoding == 'instance':
        imgProto = np.full((annotation.imgHeight, annotation.imgWidth,  1), background, np.uint16)
    else:
        imgProto = np.full((annotation.imgHeight, annotation.imgWidth,  1), background, np.uint8)

    img = imgProto.copy()
    # a dict where we keep track of the number of instances that
    # we already saw of each class
    nbInstances = {}
    for labelTuple in labels:
        if labelTuple.hasInstances:
            nbInstances[labelTuple.name] = 0

        # loop over all objects
    for obj in annotation.objects:
        label = obj.label
        polygon = obj.polygon
        # If the object is deleted, skip it
        if obj.deleted:
            continue

        # If the label is not known, but ends with a 'group' (e.g. cargroup)
        # try to remove the s and see if that works
        if (not label in name2label) and label.endswith('group'):
            label = label[:-len('group')]

        if not label in name2label:
            printError("Label '{}' not known.".format(label))

        # If the ID is negative that polygon should not be drawn
        if name2label[label].id < 0:
            continue

        if encoding == "trainIds":
            val = name2label[label].trainId
        elif encoding == "color":
            val = name2label[label].color
            #val = rgb_color[::-1]
        elif encoding == 'instance':
            isGroup = False
            if (not label in name2label) and label.endswith('group'):
                label = label[:-len('group')]
                isGroup = True
            # if this label distinguishs between invidudial instances,
            # make the id a instance ID
            if name2label[label].hasInstances and not isGroup:
                val = name2label[label].id * 1000 + nbInstances[label]
                nbInstances[label] += 1
        else:
            val = name2label[label].id

        if(len(polygon) > 0 and type(polygon[0]) is dict):
            hierarchy = polygon[0]['hierarchy']
            contours = polygon[0]['contours']
            np_hierarchy = np.array([hierarchy])
            np_contours = []
            for contour in contours:
                np_contour = np.array(contour, dtype=np.int32)
                np_contours.append(np_contour)
            cv2.drawContours(img, np_contours, -1, val, cv2.FILLED, cv2.LINE_8, np_hierarchy)
            #imgSingle = imgProto.copy()
            #cv2.drawContours(imgSingle, np_contours, -1, val, cv2.FILLED, cv2.LINE_8, np_hierarchy)
        else:
            np_contour = np.array(polygon, dtype=np.int32)
            cv2.drawContours(img, [np_contour], 0, val, cv2.FILLED)
            #imgSingle = imgProto.copy()
            #cv2.drawContours(imgSingle, [np_contour], 0, val, cv2.FILLED)

        #if(encoding == 'color'):
        #    imgGray = cv2.cvtColor(imgSingle, cv2.COLOR_BGR2GRAY)
        #elif(encoding == 'instance'):
        #    imgGray = cv2.convertScaleAbs(imgSingle)
        #else:
        #    imgGray = imgSingle.copy()

        #_, imgAlpha = cv2.threshold(imgGray, 0, 255, cv2.THRESH_BINARY)

        #kernel = np.ones((3, 3), np.uint8)
        #dilation = cv2.dilate(imgAlpha, kernel, iterations=1)
        #_, dilate_cnts, dilate_hier = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        #cv2.drawContours(img, dilate_cnts, -1, val, cv2.FILLED, cv2.LINE_8, dilate_hier)
        #cv2.drawContours(img, dilate_cnts, -1, background, 2, cv2.LINE_8, dilate_hier)

    if(encoding == 'color'):
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        return img

# A method that does all the work
# inJson is the filename of the json file
# outImg is the filename of the label image that is generated
# encoding can be set to
#     - "ids"      : classes are encoded using the regular label IDs
#     - "trainIds" : classes are encoded using the training IDs
#     - "color"    : classes are encoded using the corresponding colors
def json2img(inJson, outImg, encoding = "ids"):
    annotation = Annotation()
    annotation.fromJsonFile(inJson)
    labelImg   = createLabelImage( annotation , encoding)
    cv2.imwrite(outImg, labelImg)

# The main method, if you execute this script directly
# Reads the command line arguments and calls the method 'json2labelImg'
def main(argv):
    encoding = "ids"
    try:
        opts, args = getopt.getopt(argv,"htcil")
    except getopt.GetoptError:
        printError( 'Invalid arguments' )

    for opt, arg in opts:
        if opt == '-h':
            printHelp()
            sys.exit(0)
        elif opt == '-t':
            trainIds = "trainIds"
        elif opt == '-c':
            encoding = 'color'
        elif opt == '-i':
            encoding = 'instance'
        elif opt == '-l':
            encoding = 'label'
        else:
            printError( "Handling of argument '{}' not implementend".format(opt) )

    if len(args) == 0:
        printError( "Missing input json file" )
    elif len(args) == 1:
        printError( "Missing output image filename" )
    elif len(args) > 2:
        printError( "Too many arguments" )

    inJson = args[0]
    outImg = args[1]

    json2img( inJson , outImg, encoding)

# call the main method
if __name__ == "__main__":
    main(sys.argv[1:])
