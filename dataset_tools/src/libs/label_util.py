import os
import numpy as np
from libs.xml_io import pascal_voc_io
from libs.json_io import json_parser_io

# read label file(xml, json, coco)
# return object list[(label, vertext)] to draw


def read_label_file(file):
    if os.path.splitext(file)[1] == '.xml':
        vertex_infos = read_xml_file(file)

    if os.path.splitext(file)[1] == '.json':
        vertex_infos = read_json_file(file)

    return file.split('.')[-1], vertex_infos


def read_xml_file(file_path):
    xml_reader = pascal_voc_io.PascalVocReader(file_path)
    shapes = xml_reader.getShapes()
    bndboxs = xml_reader.getBndboxs()
    vertex_infos = []
    for shape in shapes:
        if len(shape[2]) >= 3:  # only can draw contours with more than 3 points
            vertex_infos.append((shape[0], shape[2]))  # shape[1]: points
    for bndbox in bndboxs:
        points = [(bndbox[0], bndbox[1]), (bndbox[2], bndbox[1]),
                  (bndbox[2], bndbox[3]), (bndbox[0], bndbox[3])]
        vertex_infos.append((bndbox[4], points))
    return vertex_infos


def read_json_file(file_path):
    json_reader = json_parser_io.JsonParserIO.from_file(file_path)
    vertex_infos = []
    for obj in json_reader.objects:
        bndbox = obj.bndbox
        contours = obj.contours  # for one object can have more than one contour,inside/outside contour
        parent_contour_ids = np.array(obj.hierarchy)[:, :, 3].ravel()
        for contour_id, contour in enumerate(contours):
            contour = np.array(contour)
            contour[:, :, 0] += bndbox[0]
            contour[:, :, 1] += bndbox[1]
            points = list(map(tuple, np.squeeze(contour)))
            parent_contour_id = parent_contour_ids[contour_id]
            vertex_infos.append(
                (obj.label + '\n(id:%s,parent_id:%s)' %
                 (contour_id, parent_contour_id), points))
    return vertex_infos


def read_coco_file(coco_parser, filePath):
    vertex_infos = []
    filename = os.path.basename(os.path.normpath(filePath))
    segs_with_label, category_names = coco_parser.gather_segs_with_label(filename)

    for seg_with_label in segs_with_label:
        cnt = np.reshape(seg_with_label[1], (-1, 2))
        vertex_infos.append((seg_with_label[0], list(map(tuple, cnt))))
    return vertex_infos, category_names


if __name__ == '__main__':
    read_xml_file("D:/data/2/labels/rgb_image_0.xml")
