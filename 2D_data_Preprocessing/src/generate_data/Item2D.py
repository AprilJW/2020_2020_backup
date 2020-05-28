import math
import numpy as np
import cv2
from util import img_process_util, item_algo
import copy


class Item2D_test:
    """
        represent one item

        item using in random generate 2d data, this class including
        item's image, name etc.

        Attributes:
             image: item image in 4-channel, alpha channel is item mask
             name: name of item
             is_covered: if an item is covered by others
             bndbox: bounding box of the item
             overlap_mask_img:
             subItems: for one seed include multi items,subItem only use to represent annotations,item itself using to
                        display
             mask_contour: alpah channel contours
             objArea: item origin area using for calc remain area
             keypoints: reserve


    """

    def __init__(self, item_img=None, name=None, mask_contour=None, bndbox=None, difficult=0):

        self.name = name
        self.difficult = difficult
        self.image = []
        self.is_covered = False
        self.subItems = []
        self.bndbox = []
        self.mask_contour = []
        self.overlap_mask_image = []
        self.keypoints = []
        self.skeleton = []

        if item_img is not None:
            self.image = item_img

            if bndbox is None:
                self.bndbox = [0, 0, self.image.shape[1], self.image.shape[0]]
            else:
                self.bndbox = bndbox

            b, g, r, a = cv2.split(self.image)
            self.maskContour = img_process_util.get_max_blob(a)
            self.overlap_mask_img = img_process_util.get_max_blob_bin_image(max_contour=self.maskContour, a_img=a,
                                                                            is_fill=True)
            self.image = cv2.bitwise_and(self.image, self.image, mask=self.overlap_mask_img)
            self.objArea = cv2.countNonZero(self.overlap_mask_img)
            self.rot_box = cv2.minAreaRect(self.maskContour)
        if mask_contour is not None:
            self.mask_contour = mask_contour

    def to_json(self):

        pass


class Item2D:
    """
        represent one item

        item using in random generate 2d data, this class including
        item's image, name etc.

        Attributes:
             image: item image in 4-channel, alpha channel is item mask
             name: name of item
             bndbox: bounding box of the item
             width: image width of the item
             height: image height of the item
             overlap_mask_img:

    """

    def __init__(self, item_img=None, name=None, mask_contour=None, difficult=0):
        self.image = item_img
        self.name = name
        self.difficult = difficult
        self.is_covered = False
        self.keypoints = []
        self.sub_items = []
        self.bndbox = [0, 0, 0, 0]
        self.rot_box = []
        if item_img is not None:
            self = item_algo.replace_img(self, item_img)
        else:  # mask_contour != None:
            self.maskContour = mask_contour

    def is_contain_sub_items(self):
        return len(self.sub_items) > 0
