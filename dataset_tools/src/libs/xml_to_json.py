from math import floor, ceil
import numpy as np
import logging
from PIL import Image
from tqdm import tqdm

from libs.json_io import json_parser_io
from libs.xml_io import pascal_voc_io
from libs.json_io.json_parser_io import write_json, ObjectDescInfo
from libs.dir_and_filename_info import *
from libs.image_utils import get_rotation_box
dict_name2idx = {'next': 0, 'prev': 1, 'first_child': 2, 'parent': 3}


def addContourAndChildsIntoTree(hier, trees, currentId, parentId):
    trees[parentId].append(currentId)
    childId = hier[currentId][dict_name2idx['first_child']]
    if childId != -1:
        addContourAndChildsIntoTree(hier, trees, childId, parentId)
    nextId = hier[currentId][dict_name2idx['next']]
    if nextId != -1:
        addContourAndChildsIntoTree(hier, trees, nextId, parentId)


def _get_omni_mask_from_xml(xml_full_path):
    tVocParseReader = pascal_voc_io.PascalVocReader(xml_full_path)
    shapes = tVocParseReader.shapes
    width = tVocParseReader.imgWidth
    height = tVocParseReader.imgHeight

    dict_guid2idx = {}
    hier = []
    omni_obj_anno_list = []

    for label, lineWidth, points, guid, parentGuid in shapes:
        if len(points) < 3:
            print("ignore points length is less than 3, since cannot draw contour")
            continue
        if guid not in dict_guid2idx:
            dict_guid2idx[guid] = len(dict_guid2idx)
            hier.append([-1, -1, -1, -1])
            omni_obj_anno_list.append(ObjectDescInfo())
        if parentGuid not in dict_guid2idx:
            dict_guid2idx[parentGuid] = len(dict_guid2idx)
            hier.append([-1, -1, -1, -1])
            omni_obj_anno_list.append(ObjectDescInfo())
            
        index = dict_guid2idx[guid]
        if index != dict_guid2idx[parentGuid]:
            parentIdx = dict_guid2idx[parentGuid]
            hier[index][dict_name2idx['parent']] = parentIdx

            # if parent doesn't have first child yet
            if hier[parentIdx][dict_name2idx['first_child']] == -1:
                hier[parentIdx][dict_name2idx['first_child']] = index
            else:
                # append current circle to existing last circle
                existing_lastNode = hier[parentIdx][dict_name2idx['first_child']]
                while (hier[existing_lastNode][dict_name2idx['next']] != -1):
                    existing_lastNode = hier[existing_lastNode][dict_name2idx['next']]
                hier[index][dict_name2idx['prev']] = existing_lastNode
                hier[existing_lastNode][dict_name2idx['next']] = index

        label_class = label
        arr_points = np.array(points)
        xmin, ymin, xmax, ymax = floor(min(arr_points[:, 0])), floor(min(arr_points[:, 1])), ceil(max(arr_points[:, 0])), ceil(
            max(arr_points[:, 1]))
        w = xmax - xmin
        h = ymax - ymin
        points_num = len(points)
        ins_polygon = np.zeros((points_num, 1, 2), dtype=np.float32)
        for j in range(points_num):
            ins_polygon[j, 0] = points[j]

        obj_anno = ObjectDescInfo()
        obj_anno.contours = ins_polygon
        obj_anno.label = label_class
        obj_anno.bndbox = [xmin, ymin, w, h]
        obj_anno.rot_box = get_rotation_box(ins_polygon)
        omni_obj_anno_list[dict_guid2idx[guid]] = obj_anno

    return [height, width, 3], hier, omni_obj_anno_list


def separate_object_mask(hier, omni_obj_anno_list):
    trees = []
    for treeIdi in range(len(hier)):
        trees.append([])

    for currentId in range(len(hier)):
        if hier[currentId][dict_name2idx['parent']] == -1:
            addContourAndChildsIntoTree(hier, trees, currentId, currentId)
    obj_anno_list = []
    for treeId in range(len(trees)):
        if trees[treeId]:
            old2NewIdx = [0] * len(hier)
            newIdx = 0
            for oldIdx in trees[treeId]:
                old2NewIdx[oldIdx] = newIdx
                newIdx += 1
            newHier = []
            for oldIdx in trees[treeId]:
                row = hier[oldIdx]
                for i in range(len(row)):
                    if row[i] != -1:
                        row[i] = old2NewIdx[row[i]]
                newHier.append(row)

            root_obj_anno = omni_obj_anno_list[trees[treeId][0]]
            rootContour = root_obj_anno.contours
            if len(root_obj_anno.bndbox) == 0: #todo:refactor
                continue
            xmin = float(root_obj_anno.bndbox[0])
            ymin = float(root_obj_anno.bndbox[1])
            rootContour[:, :, 0] -= xmin
            rootContour[:, :, 1] -= ymin
            contours = [rootContour]
            rootLabel = root_obj_anno.label

            for i in range(1, len(trees[treeId])):
                part_obj_anno = omni_obj_anno_list[trees[treeId][i]]
                partContour = part_obj_anno.contours
                partContour[:, :, 0] -= xmin
                partContour[:, :, 1] -= ymin
                contours.append(partContour)

            obj_anno = ObjectDescInfo()
            contours_list = []
            for cnt in contours:
                cnt = cnt.astype(int)
                if type(cnt) is not list:
                    cnt = cnt.tolist()
                contours_list.append(cnt)
            obj_anno.contours = contours_list
            obj_anno.hierarchy = [newHier]
            obj_anno.label = rootLabel
            obj_anno.bndbox = root_obj_anno.bndbox
            obj_anno.rot_box = root_obj_anno.rot_box
            obj_anno_list.append(obj_anno)
    return obj_anno_list


def xml2json(xml_full_path, image_full_path = None):
    json_full_path = os.path.splitext(xml_full_path)[0]+'.json'
    if os.path.isfile(json_full_path):
        logging.debug("targe json file already exist, skip convert:{0}".format(json_full_path))
        return
    mask_anno = json_parser_io.JsonParserIO()
    if not os.path.isfile(xml_full_path):
        im = Image.open(image_full_path)
        im_width, im_height = im.size
        mask_anno.image_shape = [im_height, im_width, 3]
        json_parser_io.write_json(mask_anno, json_full_path)
    else:
        image_shape, hier, omni_obj_anno_list = _get_omni_mask_from_xml(xml_full_path)
        mask_anno.image_shape = image_shape
        mask_anno.objects = separate_object_mask(hier, omni_obj_anno_list)
        json_parser_io.write_json(mask_anno, json_full_path)
        os.remove(xml_full_path)
    
def xmltojson_dir(dir_path):
    image_name_list = get_sorted_file_name_list(find_images_exist_path(dir_path))
    for file_name in tqdm(image_name_list, "xml to jsons: "):
        xml_full_path = get_label_file_path(dir_path, file_name, ".xml")
        xml2json(xml_full_path, os.path.join(find_images_exist_path(dir_path), file_name))

if __name__ == '__main__':
    xml2json("D://data//linkrod_finish_387_0309//labels//rgb_image_7.xml")
