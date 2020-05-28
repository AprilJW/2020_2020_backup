import math
import os
import shutil
import sys
import yaml
import cv2
import numpy as np
import json
import logging

from libs.dir_and_filename_info import get_sorted_file_name_list
from enum import Enum
# path management


class DATASET_TYPES(Enum):
    UNKNOWN = 0
    HUB = 1
    VOC = 2
    COCO = 3
    CS = 4

color_pallete = [0, 0, 0,
                 128, 0, 0,
                 0, 128, 0,
                 128, 128, 0,
                 0, 128, 128,
                 128, 128, 128,
                 64, 0, 0,
                 192, 0, 0,
                 64, 128, 0,
                 192, 128, 0,
                 64, 0, 128,
                 192, 0, 128,
                 64, 128, 128,
                 192, 128, 128,
                 0, 64, 0,
                 128, 64, 0,
                 0, 192, 0,
                 128, 192, 0,
                 0, 64, 128, ]


def write_label_id_color_file(label_list, dest_path):
    dest_file_path = os.path.join(dest_path, 'label_id_color.json')
    label_id_color = {}
    for id, label_name in enumerate(label_list):
        label_id_color[label_name] = {
            'id': id + 1,
            'color': color_pallete[3 * id + 3: 3 * id + 6]
        }

    with open(dest_file_path, 'w+') as label_id_color_file:
        label_id_color_file.write(json.dumps(label_id_color))


def get_unique_key(one_element_dict):
    return list(one_element_dict.keys())[0]


def create_dirs_delete_old(root_path):
    if os.path.exists(root_path):
        shutil.rmtree(root_path)
    os.makedirs(root_path)


def recusive_create_dirs(parent, children):
    if not children:
        return

    for child in children.keys():
        cpath = os.path.join(parent, child)
        name, ext = os.path.splitext(child)
        if ext:
            with open(cpath, 'w+') as file:
                pass
        else:
            os.makedirs(cpath)

        recusive_create_dirs(cpath, children[child])


def create_workspace_dirs(root_path, sub_dirs):
    create_dirs_delete_old(root_path)
    for k, v in sub_dirs.items():
        print({k: v})
        recusive_create_dirs(root_path, {k: v})


# copy image and resize
def copy_image(area, img_in, dest_file, bg_color):
    if area[0] >= 0 and area[1] >= 0:
        copied_img = img_in[area[1]:area[3], area[0]:area[2]]
    else:
        left_border = right_border = top_border = bottom_border = 0
        img_inter = img_in.copy()

        if area[0] < 0:
            left_border = 0 - area[0]
            right_border = area[2] - img_in.shape[1]
        else:
            img_inter = img_in[0:img_in.shape[0], area[0]:area[2]].copy()

        if area[1] < 0:
            top_border = 0 - area[1]
            bottom_border = area[3] - img_in.shape[0]
        else:
            img_inter = img_in[area[1]:area[3], 0:img_in.shape[1]].copy()
        copied_img = cv2.copyMakeBorder(img_inter, top=top_border, bottom=bottom_border, left=left_border,
                                        right=right_border, borderType=cv2.BORDER_CONSTANT, value=bg_color)

    cv2.imwrite(os.path.join(dest_file), copied_img)


def get_images_list(src_path):
    logging.info('get images list...')
    return get_sorted_file_name_list(src_path)


# get area of new image on old sized image
def get_area(shape, width, height):
    x1 = (int(shape[1]) - width) / 2
    x2 = (int(shape[1]) + width) / 2
    y1 = (int(shape[0]) - height) / 2
    y2 = (int(shape[0]) + height) / 2

    # print(x1, x2, y1, y2)
    if x1 >= 0:
        x1 = math.floor(x1)
    else:
        x1 = math.ceil(x1)
    if y1 >= 0:
        y1 = math.floor(y1)
    else:
        y1 = math.ceil(y1)

    x2 = math.ceil(x2)
    y2 = math.ceil(y2)

    return int(x1), int(y1), int(x2), int(y2)


def is_valid_mask_anno(img_object):
    if img_object.is_covered:
        return False
    if (img_object.contours is None) or len(img_object.contours) == 0:
        return False
    if (img_object.hierarchy is None) or len(img_object.hierarchy) == 0:
        return False
    if img_object.label == 'bg':
        return False
    if int(img_object.bndbox[2]) < 2 or int(img_object.bndbox[3]) < 2:
        return False
    return True


def get_object_bbox(bndbox, x1, y1):
    bbox = [int(bndbox[0] - x1), int(bndbox[1] - y1), int(bndbox[2]), int(bndbox[3])]
    for i in range(len(bbox)):
        bbox[i] = max(bbox[i], 0)
    return bbox


def _update_contours_with_divider(seg_img, anno_objects, cnts_hier):
    # reconstruct (contours, hierarchy) pair for each mask as the out contour
    # is changed after above processing
    single_seg_img = np.zeros(seg_img.shape, np.uint8)
    for obj_id, anno_object in enumerate(anno_objects):
        if is_valid_mask_anno(anno_object):
            single_seg_img.fill(0)
            contours = cnts_hier[obj_id][0]
            hierarchy = cnts_hier[obj_id][1]
            out_cnt_id = -1
            max_out_contour = []
            for i in range(len(contours)):
                if hierarchy[0][i][3] < 0 and (len(contours[i]) > len(max_out_contour)):
                    out_cnt_id = i
                    max_out_contour = contours[i].copy()

            cv2.drawContours(single_seg_img, [max_out_contour], 0, 255, cv2.FILLED, cv2.LINE_8)
            single_seg_img = cv2.bitwise_and(single_seg_img, seg_img)
            _, obj_contours, _ = cv2.findContours(
                single_seg_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if len(obj_contours) == 0:
                return
            max_contour = np.array([])
            for i in range(len(obj_contours)):
                if len(obj_contours[i]) > len(max_contour):
                    max_contour = obj_contours[i].copy()
            contours[out_cnt_id] = max_contour


def _parse_pickle_mask(anno_object, area):
    if isinstance(anno_object.maskContour, dict):
        contours = anno_object.maskContour['contours']
        hierarchy = anno_object.maskContour['hierarchy']
    else:
        contours = anno_object.maskContour
        cnts = np.array(contours)
        hierarchy = [[[-1, -1, -1, -1]]]
        if len(cnts.shape) == 3:
            contours = [contours]
        elif len(cnts.shape) == 4:
            # for i in range(len(cnts.shape[0])):
            #     hierarchy.append([[-1, -1, -1, -1]])
            print('multiple parts mask are not supported currently:', cnts.shape)
            sys.exit()
        else:
            print('mask contour from pickle has shape:', cnts.shape)
            sys.exit()

        hierarchy = np.array(hierarchy)
    for id, contour in enumerate(contours):
        contour[:, :, 0] += (anno_object.bndbox[0] - area[0])
        contour[:, :, 1] += (anno_object.bndbox[1] - area[1])
        contours[id] = contour.astype(int)

    return contours, hierarchy


def _draw_segmentation_image(seg_img, contours, hierarchy, separation_linewidth):
    # only contains mask for one object
    cv2.drawContours(seg_img, contours, -1, 255, cv2.FILLED, cv2.LINE_8, hierarchy, 1)
    if separation_linewidth == 0:
        return seg_img
    single_seg_img = np.zeros(seg_img.shape, np.uint8)
    cv2.drawContours(single_seg_img, contours, -1, 255, cv2.FILLED, cv2.LINE_8, hierarchy, 1)
    _, img_alpha = cv2.threshold(single_seg_img, 0, 255, cv2.THRESH_BINARY)
    ksize = 2 * separation_linewidth + 1
    kernel = np.ones((ksize, ksize), np.uint8)
    alpha_dilate = cv2.dilate(img_alpha, kernel, iterations=1)
    sep_line = cv2.bitwise_not(cv2.bitwise_xor(img_alpha, alpha_dilate))
    seg_img = cv2.bitwise_and(seg_img, sep_line)
    return seg_img


# separate contours by drawing a black line around all objects
def _find_separate_contours_from_file(area, anno_objects, separation_linewidth):
    if anno_objects is None or len(anno_objects) == 0:
        return []
    obj_cnts_desc_list = []
    width = area[2] - area[0]
    height = area[3] - area[1]
    # contains masks for all objects recognized as masks
    seg_img = np.zeros((height, width, 1), np.uint8)
    # separate contours by drawing a black line around all objects
    for anno_object in anno_objects:
        if is_valid_mask_anno(anno_object):
            contours = anno_object.contours
            hierarchy = np.array(anno_object.hierarchy)
            for id, contour in enumerate(contours):
                contour = np.array(contour)
                contour[:, :, 0] += (anno_object.bndbox[0] - area[0])
                contour[:, :, 1] += (anno_object.bndbox[1] - area[1])
                contours[id] = contour.astype(int)
            seg_img = _draw_segmentation_image(
                seg_img, contours, hierarchy, separation_linewidth)
            obj_cnts_desc_list.append([contours, hierarchy, anno_object.label])
        else:
            obj_cnts_desc_list.append([[], None, ''])

    if separation_linewidth > 0:
        _update_contours_with_divider(seg_img, anno_objects, obj_cnts_desc_list)

    return obj_cnts_desc_list


def get_masks_from_file(area, anno_objects, separation_linewidth, label_list):
    width = area[2] - area[0]
    height = area[3] - area[1]
    # find new contours of all separated masks
    obj_cnts_desc_list = _find_separate_contours_from_file(
        area, anno_objects, separation_linewidth)
    # draw the segmentation image of object masks
    seg_img = np.zeros((height, width, 1), np.uint8)
    for contours, hierarchy, label in obj_cnts_desc_list:
        if label:
            if label not in label_list:
                label_list.append(label)
            cv2.drawContours(seg_img, contours, -1, label_list.index(label) +
                             1, cv2.FILLED, cv2.LINE_8, hierarchy)

    return seg_img, obj_cnts_desc_list


def get_config_data(config_filename):
    with open(config_filename, "r") as config_file:
        data = yaml.load(config_file)
    return data


def get_mode_last_id(mode_last_id, image_largest_id):
    try:
        mode_set_num = int(mode_last_id)
        if mode_set_num > image_largest_id:
            print(mode_last_id, 'in train_val_ratios is too large')
            sys.exit()
    except ValueError:
        print(mode_last_id, 'in train_val_ratios cannot convert to integer')
        sys.exit()

    return mode_set_num


def get_image_id(srcfile):
    filename, ext = os.path.splitext(srcfile)
    img_id = int(filename.split('_')[-1])
    return img_id


def get_mode_num(mode_last_id, images_list):
    images_total_num = len(images_list)
    image_largest_id = get_image_id(images_list[images_total_num - 1])
    train_bound_id = get_mode_last_id(mode_last_id, image_largest_id)
    train_num = 0
    for i in range(len(images_list)):
        image_id = get_image_id(images_list[i])
        if image_id == train_bound_id:
            train_num = i + 1
            break
        elif image_id > train_bound_id:
            train_num = i
            break
    return train_num


def find_inner_cnt(obj_cnts, obj_hier):
    inner_cnt = None
    for i in range(len(obj_hier[0])):
        if obj_hier[0][i][3] >= 0:
            inner_cnt = obj_cnts[i]
            break
    return inner_cnt


def count_inner_cnts(part_hier):
    inner_cnts_num = 0
    for i in range(len(part_hier[0])):
        if part_hier[0][i][3] >= 0:
            inner_cnts_num += 1

    return inner_cnts_num


def separate_img_by_line(single_seg_img, startX, endX, startY, endY):
    object_points = cv2.findNonZero(single_seg_img)
    assert object_points is not None

    upper_img = np.zeros_like(single_seg_img)
    lower_img = np.zeros_like(single_seg_img)
    for point in object_points:
        x = point[0][0]
        y = point[0][1]
        f = (y - endY) * (startX - endX) - (x - endX) * (startY - endY)
        if f > 0:
            upper_img[y, x] = 255
        elif f < 0:
            lower_img[y, x] = 255
        else:
            upper_img[y, x] = 255
            lower_img[y, x] = 255

    return upper_img, lower_img


def get_same_name_file(src_path, match_filename):
    depth_srcfiles = os.listdir(src_path)
    filename, ext = os.path.splitext(match_filename)
    depth_srcfile = match_filename
    for depth_file in depth_srcfiles:
        if filename in depth_file:
            depth_srcfile = depth_file
            break
    
    return depth_srcfile
    