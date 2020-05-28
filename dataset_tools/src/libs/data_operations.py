import os
import cv2
import numpy as np
import copy
from tqdm import tqdm
from libs.xml_io import pascal_voc_io
from libs import json_to_xml, xml_to_json
from libs.dir_and_filename_info import *
from libs.image_utils import cal_bndbox_max_length
from libs.check_dataset_valid import check_rgb_depth_size_match


def affine_on_point(p, M):
    result = np.matmul(M, np.array([p[0], p[1], 1]).T).astype(np.int)
    return (result[0], result[1])


def affine_on_xml_shapes(xml_shapes, M):
    i_pts = 2  # index of contour points in xml_shape
    for xml_shape in xml_shapes:
        for j in range(len(xml_shape[i_pts])):
            xml_shape[i_pts][j] = affine_on_point(xml_shape[i_pts][j], np.array(M))
    # Better ways to implement? Because xml_shape is a tuple, we can't
    # modify xml_shape[i_pts], have to modify xml_shape[i_pts][j].
    return xml_shapes


def calc_area_from_points(points, need_offset=False):
    ins_polygon = np.zeros((len(points), 1, 2), dtype=np.float64)
    for j in range(len(points)):
        ins_polygon[j, 0] = points[j]
    if need_offset:
        countour = ins_polygon.astype(np.int32) + np.ones(ins_polygon.shape,
                                                          np.int32) * 300  # to make sure point value > 0
    else:
        countour = ins_polygon.astype(np.int32)
    return cv2.contourArea(countour)


def refind_contour(points, width, height):
    if all(p[0]>=0 and p[0]<width and p[1]>=0 and p[1]<height for p in points):
        return copy.deepcopy(points)
    
    blank = np.zeros((height, width), np.uint8)
    cv2.fillPoly(blank, np.array([points]), 255)
    _, contours, _ = cv2.findContours(blank, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 1:
        print('The object has more than 1 fragments, do not support that for now')
        return []
    return np.squeeze(contours)


def remove_shapes_out_of_image(width, height, shapes, remain_ratio_in_aug=1.0):
    indices_of_shapes_out_of_image = []
    for i, shape in enumerate(shapes):
        points = shape[2]  # [(x1, y1), (x2, y2)...]
        ori_area = calc_area_from_points(points, True)
        if ori_area == 0:
            continue
        
        new_points = refind_contour(points, width, height)
        after_area = calc_area_from_points(new_points)
        if after_area / ori_area < remain_ratio_in_aug:
            indices_of_shapes_out_of_image.append(i)
        else:
            shape[2].clear()
            for item_point in new_points:
                shape[2].append(item_point)

    indices_of_shapes_out_of_image = set(indices_of_shapes_out_of_image)

    # assume a shape has only children, no grandchildren or great-grandchildren and so on
    child_indices = [[] for _ in range(len(shapes))]
    parent_indices = np.ones(len(shapes)) * -1
    for parent_idx, parent_shape in enumerate(shapes):
        for child_idx, child_shape in enumerate(shapes):
            if child_shape[-1] == parent_shape[-2]:  # child_shape.parentGuid == parent_shape.guid
                parent_indices[child_idx] = parent_idx
                child_indices[parent_idx].append(child_idx)
    for index in range(len(shapes)):
        # if its child is in the set, the parent should also be pulled to the set
        for child_idx in child_indices[index]:
            if child_idx in indices_of_shapes_out_of_image:
                indices_of_shapes_out_of_image.add(index)
        # if its parent is in the set, the child should also be pulled to the set
        if parent_indices[index] in indices_of_shapes_out_of_image:
            indices_of_shapes_out_of_image.add(index)

    remaining_shapes_indices = set(range(len(shapes)))
    remaining_shapes_indices.difference_update(indices_of_shapes_out_of_image)
    remaining_shapes = [shapes[i] for i in remaining_shapes_indices]
    return remaining_shapes


def read_depth_image(depth_file, thres=1e5):
    if not depth_file or not os.path.isfile(depth_file):
        return None
    depth_image = cv2.imread(depth_file, cv2.IMREAD_UNCHANGED)
    # For 32FC1 image saved as 8UC4
    if len(depth_image.shape) > 2: 
        depth_image = depth_image.view(dtype=np.float32)
        depth_image = np.squeeze(depth_image)
    # For strange value
    if np.max(depth_image) > thres:
        raise Exception('Max value ({0}) of {1} is too large to be true (larger than {2})'.format(np.max(depth_image), depth_file, thres))
    return depth_image


def save_depth_image(depth_file, depth_image):
    # For 32FC1 image to save as 8UC4
    if depth_image.dtype == np.float32: 
        cols, rows = depth_image.shape
        depth_image = depth_image.view(dtype=np.uint8).reshape((cols, rows, 4))
    cv2.imwrite(depth_file, depth_image)
    
        
class dl_data:

    def __init__(self, data_file):
        image_file, label_file, depth_file = data_file
        # Read image
        self.image = cv2.imread(image_file)
        # Read depth
        self.depth = read_depth_image(depth_file)
        # Read label
        if not os.path.isfile(label_file):
            self.xml_shapes = None
        else:
            # Change json to xml so that we only need to deal with 1 type of file
            is_json = label_file.endswith(EXT_JSON)
            if is_json:
                json_to_xml.json2xml(label_file, image_file, XML_TYPE_VERTEX)
                label_file = os.path.splitext(label_file)[0] + EXT_XML
            self.xml_shapes = pascal_voc_io.PascalVocReader(label_file).shapes
            if is_json:
                xml_to_json.xml2json(label_file, image_file)

    def save_to(self, data_file):
        image_file, label_file, depth_file = data_file
        # Save image
        cv2.imwrite(image_file, self.image)
        # Save depth
        if self.depth is not None:
            save_depth_image(depth_file, self.depth)
        # Save label
        if self.xml_shapes is not None:
            is_json = label_file.endswith(EXT_JSON)
            if is_json:
                label_file = os.path.splitext(label_file)[0] + EXT_XML
            folder_name, file_name = os.path.split(label_file)
            pw = pascal_voc_io.PascalVocWriter(folder_name, file_name, self.image.shape)
            for xml_shape in self.xml_shapes:
                pw.addVertexs(xml_shape[0], xml_shape[1], xml_shape[2], xml_shape[3], xml_shape[4])
            pw.save(label_file)
            # Change xml back to json if need
            if is_json:
                xml_to_json.xml2json(label_file, image_file)

    def resize_by_size(self, width, height):
        ratio_width = width / self.image.shape[1]
        ratio_height = height / self.image.shape[0]
        # Deal with image
        self.image = cv2.resize(self.image, (width, height),
                                interpolation=cv2.INTER_LINEAR)
        # Deal with depth
        if self.depth is not None:
            self.depth = cv2.resize(self.depth, (width, height),
                                    interpolation=cv2.INTER_NEAREST)
        # Deal with label
        if self.xml_shapes is not None:
            M = np.array([[ratio_width, 0, 0], [0, ratio_height, 0]], dtype=float)
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)

    def resize_by_scale(self, scale_ratio):
        # Deal with image
        self.image = cv2.resize(self.image, None, fx=scale_ratio, fy=scale_ratio, 
                                interpolation=cv2.INTER_LINEAR)
        # Deal with depth
        if self.depth is not None:
            self.depth = cv2.resize(self.depth, None, fx=scale_ratio, fy=scale_ratio, 
                                    interpolation=cv2.INTER_NEAREST)
        # Deal with label
        if self.xml_shapes is not None:
            M = np.array([[scale_ratio, 0, 0], [0, scale_ratio, 0]], dtype=float)
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)

    def fill(self, left, top, width, height, padding_color=(0, 0, 0)):
        bottom = height - self.image.shape[0] - top
        right = width - self.image.shape[1] - left
        # Deal with image
        self.image = cv2.copyMakeBorder(self.image, top, bottom, left, right, 
                                        borderType=cv2.BORDER_CONSTANT, value=padding_color)
        # Deal with depth
        if self.depth is not None:
            self.depth = cv2.copyMakeBorder(self.depth, top, bottom, left, right, 
                                            borderType=cv2.BORDER_CONSTANT, value=padding_color)
        # Deal with label
        if self.xml_shapes is not None:
            M = np.array([[1, 0, left], [0, 1, top]])
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)

    def crop(self, left, top, width, height, remain_ratio_in_aug=1.0):
        # Deal with image
        self.image = self.image[top:top + height, left:left + width]
        # Deal with depth
        if self.depth is not None:
            self.depth = self.depth[top:top + height, left:left + width]
        # Deal with label
        if self.xml_shapes is not None:
            M = np.array([[1, 0, -left], [0, 1, -top]])
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)
            new_height, new_width = self.image.shape[:2]
            self.xml_shapes = remove_shapes_out_of_image(
                new_width, new_height, self.xml_shapes, remain_ratio_in_aug)

    def rotate_and_scale_keep_size(self, rotation_angle, scale_ratio, padding_color, remain_ratio_in_aug=1.0):
        height, width = self.image.shape[:2]
        M = cv2.getRotationMatrix2D((width / 2, height / 2), rotation_angle, scale_ratio)
        # Deal with image
        self.image = cv2.warpAffine(self.image, M, (width, height), flags=cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_CONSTANT, borderValue=padding_color)
        # Deal with depth
        if self.depth is not None:
            self.depth = cv2.warpAffine(self.depth, M, (width, height), flags=cv2.INTER_NEAREST,
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=padding_color)
        # Deal with label
        if self.xml_shapes is not None:
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)
            self.xml_shapes = remove_shapes_out_of_image(
                width, height, self.xml_shapes, remain_ratio_in_aug)

    def translate_keep_size(self, trans_width, trans_height, padding_color, remain_ratio_in_aug=1.0):
        height, width = self.image.shape[:2]
        M = np.float32([[1, 0, trans_width], [0, 1, trans_height]])
        # Deal with image
        self.image = cv2.warpAffine(self.image, M, (width, height),
                                    borderMode=cv2.BORDER_CONSTANT, borderValue=padding_color)
        # Deal with depth
        if self.depth is not None:
            self.depth = cv2.warpAffine(self.depth, M, (width, height),
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=padding_color)
        # Deal with label
        if self.xml_shapes is not None:
            self.xml_shapes = affine_on_xml_shapes(self.xml_shapes, M)
            self.xml_shapes = remove_shapes_out_of_image(
                width, height, self.xml_shapes, remain_ratio_in_aug)

    def change_contrast_and_brightness(self, contrast, brightness):
        self.image = self.image.astype(float)
        self.image = contrast * (self.image - 128) + 128 + brightness
        self.image = np.where(self.image > 255, 255, self.image)
        self.image = np.where(self.image < 0, 0, self.image)
        self.image = self.image.astype(np.uint8)


def augment(src_dir, dst_dir, brightness, contrast, scale, rotation, translation, 
            padding_color, aug_times, remain_ratio_in_aug=1.0):
    aug_dir = dir_parser(src_dir, dst_dir)
    check_rgb_depth_size_match(src_dir)

    idx = 0
    for data_name in tqdm(aug_dir.all_data_names(), "augment data:"):
        for _ in range(aug_times):
            data = dl_data(aug_dir.get_src_files_by_name(data_name))
            
            # Random rotation & scale
            rotation_angle = np.random.uniform(rotation[0], rotation[1])
            scale_ratio = np.random.uniform(float(1 + scale[0] / 100), float(1 + scale[1] / 100))
            data.rotate_and_scale_keep_size(rotation_angle, scale_ratio, padding_color, remain_ratio_in_aug)
            
            # Random translation
            trans_width = np.random.uniform(translation[0], translation[1])
            trans_height = np.random.uniform(translation[0], translation[1])
            data.translate_keep_size(trans_width, trans_height, padding_color, remain_ratio_in_aug)
            
            # Random brightness & contrast
            delta_brightness = np.random.uniform(float(brightness[0]), float(brightness[1]))
            contrast_ratio = np.random.uniform(float(1 + contrast[0] / 100), float(1 + contrast[1] / 100))
            data.change_contrast_and_brightness(contrast_ratio, delta_brightness)
            
            data.save_to(aug_dir.get_dst_files_by_name(voc_name(idx)))
            idx = idx + 1
    
    # Copy original data
    for data_name in tqdm(aug_dir.all_data_names(), "copy original data:"):
        data = dl_data(aug_dir.get_src_files_by_name(data_name))
        data.save_to(aug_dir.get_dst_files_by_name(voc_name(idx)))
        idx = idx + 1


def warp(src_dir, dst_dir, resize_mode=None, padding_color=None, new_width=None, new_height=None,
                   scale_ratio=1.0,
                   roi=[0] * 4, example_file_path=None):
    resize_dir = dir_parser(src_dir, dst_dir)
    check_rgb_depth_size_match(src_dir)

    for data_name in tqdm(resize_dir.all_data_names(), "resize images:"):
        data = dl_data(resize_dir.get_src_files_by_name(data_name))

        if resize_mode == RESIZE_MODE_FILL:
            height, width = data.image.shape[:2]
            square_size = max(width, height)
            left, top = (square_size - width) // 2, (square_size - height) // 2
            data.fill(left, top, square_size, square_size, padding_color)
            data.resize_by_size(new_width, new_height)

        elif resize_mode == RESIZE_MODE_CROP:
            height, width = data.image.shape[:2]
            square_size = min(width, height)
            left, top = (width - square_size) // 2, (height - square_size) // 2
            data.crop(left, top, square_size, square_size)
            data.resize_by_size(new_width, new_height)

        elif resize_mode == RESIZE_MODE_PLAIN:
            data.resize_by_scale(scale_ratio)

        elif resize_mode == RESIZE_MODE_ROI:
            data.crop(roi[0], roi[1], roi[2], roi[3])
            data.resize_by_scale(scale_ratio)
            height, width = data.image.shape[:2]
            left, top = (new_width - width) // 2, (new_height - height) // 2
            data.fill(left, top, new_width, new_height, padding_color)

        elif resize_mode == RESIZE_MODE_FILE:
            example_img = cv2.imread(example_file_path, cv2.IMREAD_UNCHANGED)
            ratio = cal_bndbox_max_length(example_img) / cal_bndbox_max_length(data.image)
            data.resize_by_scale(ratio)

        data.save_to(resize_dir.get_dst_files_by_name(data_name))
