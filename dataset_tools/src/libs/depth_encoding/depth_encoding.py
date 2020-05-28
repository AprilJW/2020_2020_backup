import os
import cv2
import numpy as np
from tqdm import tqdm
from libs.depth_encoding.jet_colormap import apply_jet_mapping
from libs.depth_encoding.depth_noise import depth_noisy
from libs.depth_encoding.exr_to_jpg import cvt_to_8uc1
from libs.depth_encoding.depth_type import DEPTH_FILE_TYPE, DEPTH_ENCODE_TYPE
from libs.dir_and_filename_info import depth_extensions, get_sorted_file_name_list


def start_depth_encoding(src_path, dest_path, depth_src_type, encode_type, min_max):
    os.makedirs(dest_path, exist_ok=True)
    file_list_depth = get_sorted_file_name_list(src_path)
    for filename in tqdm(file_list_depth):
        filepath = os.path.join(src_path, filename)
        if os.path.splitext(filename)[1] in depth_extensions:
            if depth_src_type == DEPTH_FILE_TYPE.EXR.value:
                image_depth = depth_noisy(filepath, min_max)
            else:
                image_depth = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
                image_depth = cvt_to_8uc1(image_depth, cvt_method=min_max)
            image_depth_encoded = image_depth
            if encode_type == DEPTH_ENCODE_TYPE.JET_MAPPING.value:
                image_depth_encoded = apply_jet_mapping(image_depth)
            dest_filepath = os.path.join(dest_path, os.path.splitext(filename)[0] + '.jpg')
            print(dest_filepath)
            cv2.imwrite(dest_filepath, image_depth_encoded)
        elif os.path.isdir(filepath):
            sub_dest_path = os.path.join(dest_path, filename)
            os.makedirs(sub_dest_path, exist_ok=True)
            start_depth_encoding(filepath, sub_dest_path, depth_src_type, encode_type, min_max)
