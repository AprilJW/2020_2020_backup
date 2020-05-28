import os, sys
import numpy as np
import cv2
import uuid
import logging
from libs.json_io.json_parser_io import JsonParserIO, ObjectDescInfo
from libs.xml_io import pascal_voc_io
from libs.dir_and_filename_info import *
from tqdm import tqdm

def _write_mask_anno_to_xml(mask_anno, xml_full_path, jpg_full_path = None, xml_type = XML_TYPE_MIX):
    pw = pascal_voc_io.PascalVocWriter(xml_full_path, jpg_full_path, mask_anno.image_shape, "mechmind")
    for obj_anno in mask_anno.objects:
        xmax = obj_anno.bndbox[0] + obj_anno.bndbox[2]
        ymax = obj_anno.bndbox[1] + obj_anno.bndbox[3]
        #obj_item.bndbox = [obj_anno.bndbox[0], obj_anno.bndbox[1], xmax, ymax]
        contours = obj_anno.contours.copy()
        max_cnt = np.array([])
        max_cnt_area = 0
        
        id_to_guid = {}
        for id, contour in enumerate(contours):
            guid = uuid.uuid4()
            parent_guid = guid
            contour = np.array(contour)
            contour[:, :, 0] += obj_anno.bndbox[0]
            contour[:, :, 1] += obj_anno.bndbox[1]
            contour = contour.astype(int)
            cnt_area = cv2.contourArea(contour)
            id_to_guid[id] = guid
            if obj_anno.hierarchy[0][id][3] < 0 and cnt_area > max_cnt_area:
                max_cnt = contour.copy()
                max_cnt_area = cnt_area
            if obj_anno.hierarchy[0][id][3] >= 0:
                #contour has parent contour
                if id in id_to_guid:
                    parent_guid = id_to_guid[obj_anno.hierarchy[0][id][3]]
            
            rot_box = cv2.minAreaRect(max_cnt)
            cx = int(round(rot_box[0][0])) + obj_anno.bndbox[0]
            cy = int(round(rot_box[0][1])) + obj_anno.bndbox[1]
            w = int(round(rot_box[1][0]))
            h = int(round(rot_box[1][1]))
            theta = int(round(rot_box[2]))
            
            #if has rot_box in json, use exist rot_box
            if len(obj_anno.rot_box) > 0:
                [cx, cy], [w, h], theta = obj_anno.rot_box
                
            points = list(map(tuple, np.squeeze(contour)))
            if xml_type == XML_TYPE_VERTEX:
                pw.addVertexs(obj_anno.label, 2, points, guid, parent_guid)
            elif xml_type == XML_TYPE_BNDBOX:
                pw.addBndBox(obj_anno.bndbox[0], obj_anno.bndbox[1], xmax, ymax, cx, cy, w, h, theta, obj_anno.label)
            else:
                pw.addVertexs(obj_anno.label, 2, points, guid, parent_guid)
                pw.addBndBox(obj_anno.bndbox[0], obj_anno.bndbox[1], xmax, ymax, cx, cy, w, h, theta, obj_anno.label)

    pw.save(xml_full_path)


def json2xml(json_full_path, jpg_full_path = None, xml_type = XML_TYPE_MIX):
    if not os.path.isfile(json_full_path):
        logging.debug("src json file not exist")
        return
    xml_full_path = os.path.splitext(json_full_path)[0]+'.xml'
    if os.path.isfile(xml_full_path):
        logging.debug("targe xml file already exist, skip convert:{0}".format(xml_full_path))
        return
    mask_anno = JsonParserIO.from_file(json_full_path)
    _write_mask_anno_to_xml(mask_anno, xml_full_path, jpg_full_path, xml_type)
    os.remove(json_full_path)
    
def jsontoxml_dir(dir_path, xml_type = XML_TYPE_MIX):
    image_name_list = get_sorted_file_name_list(find_images_exist_path(dir_path))
    for file in tqdm(image_name_list, "json to xml: "):
        json_full_path= get_label_file_path(dir_path, file, ".json")
        json2xml(json_full_path, file, xml_type) #file: jpg full path

            
if __name__ == '__main__':
    json2xml("D://data//linkrod_finish_387_0309//labels//rgb_image_7.json", "rgb_image_4.json")
