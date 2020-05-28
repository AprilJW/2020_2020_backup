import os
from PIL import Image
import numpy as np
from libs.dir_and_filename_info import *


def check_if_images_labels(dir_path):
    return is_images_path_exist(dir_path) and is_labels_path_exist(dir_path)


def check_if_file_name_valid(dir_path):
    image_name_list = get_sorted_file_name_list(find_images_exist_path(dir_path))
    return all(img_name.startswith("2007_") for img_name in image_name_list)


def check_if_json_labeled(dir_path):
    label_name_list = get_sorted_file_name_list(find_labels_exist_path(dir_path))
    return all(os.path.splitext(label_file)[1] == '.json' for label_file in label_name_list)


def get_pixel_unique_values(dir_path):
    image_name_list = get_sorted_file_name_list(find_images_exist_path(dir_path))
    key_list = []
    for image in image_name_list:
        image_full_path = os.path.join(dir_path, image)
        mask_img = Image.open(image_full_path)
        arr = np.array(mask_img)
        key_list += np.unique(arr).tolist()

    return set(key_list)


def check_rgb_depth_size_match(dir_path):
    rgb_dir = get_dir_path(dir_path, DIR_IMAGES)
    depth_dir = get_dir_path(dir_path,DIR_DEPTH)
    if not os.path.isdir(rgb_dir) or not os.listdir(rgb_dir):
        raise ValueError("No RGB images!")
    if not os.path.isdir(depth_dir) or not os.listdir(depth_dir):
        return True
    with Image.open(os.path.join(rgb_dir,os.listdir(rgb_dir)[0])) as rgb_img:
        rgb_size = rgb_img.size
    with Image.open(os.path.join(depth_dir,os.listdir(depth_dir)[0])) as depth_img:
        depth_size = depth_img.size
    if rgb_size != depth_size:
        raise ValueError("RGB and Depth images have different shapes!")
    return True
        
    
if __name__ == '__main__':
    print(check_if_images_labels(r"D:\data\augment"))
