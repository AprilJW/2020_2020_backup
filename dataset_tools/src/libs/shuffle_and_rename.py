import os
import random
import logging
from tqdm import tqdm
from libs.dir_and_filename_info import *

def shuffle_and_rename(src_dir, dest_dir, baseIdx=0, name_type = VOC):
    if not is_images_path_exist(src_dir) or not is_labels_path_exist(src_dir):
        split_dir_to_images_labels(src_dir)
    
    if not is_images_path_exist(dest_dir) or not is_labels_path_exist(dest_dir):
        split_dir_to_images_labels(dest_dir)
    
    src_images_path = os.path.join(src_dir, DIR_IMAGES)
    src_labels_path = os.path.join(src_dir, DIR_LABELS)
    src_depth_path = os.path.join(src_dir, DIR_DEPTH)
    dest_images_path = get_dir_path(dest_dir, DIR_IMAGES, create_if_not_exist= True)
    dest_labels_path = get_dir_path(dest_dir, DIR_LABELS, create_if_not_exist= True)
    if os.path.exists(src_depth_path):
        dest_depth_path = get_dir_path(dest_dir, DIR_DEPTH, create_if_not_exist=True)
    
    if os.listdir(src_labels_path) != []:
        label_suffix = '.' + os.listdir(src_labels_path)[0].split('.')[-1]
    else:
        label_suffix = ''

    depth_suffix = ''
    if os.path.exists(src_depth_path):
        if len(os.listdir(src_depth_path)) > 0:
            depth_suffix = '.' + os.listdir(src_depth_path)[0].split('.')[-1]

    #shuffle
    imgs = os.listdir(src_images_path)
    random.shuffle(imgs)
    for count, img in tqdm(enumerate(imgs), "shuffle"):
        img_suffix = '.' + img.split('.')[-1]
        #get new name
        if name_type == VOC:
            img_new_base_name = voc_name(baseIdx+count)
        elif name_type == RGB:
            img_new_base_name = rgb_image_name(baseIdx+count)
        else:
            img_new_base_name = uuid_name()

        #rename image
        os.rename(os.path.join(src_images_path, img), os.path.join(dest_images_path, img_new_base_name + img_suffix))
        
        #rename label
        label_absolute_path = os.path.join(src_labels_path, img.split('.')[0] + label_suffix)
        if os.path.isfile(label_absolute_path):
            os.rename(label_absolute_path, os.path.join(dest_labels_path, img_new_base_name + label_suffix)) #rename label

        if os.path.exists(src_depth_path):
            depth_absolute_path = os.path.join(src_depth_path, img.split('.')[0] + depth_suffix)
            if os.path.isfile(depth_absolute_path):
                os.rename(depth_absolute_path, os.path.join(dest_depth_path, img_new_base_name + depth_suffix))
            
def shuffle_and_rename_local(src_dir, baseIdx=0, name_type = VOC):
    tmp_dir = os.path.join(src_dir, "tmp_dir")
    os.makedirs(tmp_dir, exist_ok = True)

    tmp_images_dir = get_dir_path(tmp_dir, DIR_IMAGES, True)
    tmp_labels_dir = get_dir_path(tmp_dir, DIR_LABELS, True)
    depth_src_path = os.path.join(src_dir, DIR_DEPTH)
    if os.path.exists(depth_src_path):
        tmp_depth_dir = get_dir_path(tmp_dir, DIR_DEPTH, True)
    
    move_files(os.path.join(src_dir, DIR_IMAGES), tmp_images_dir)
    move_files(os.path.join(src_dir, DIR_LABELS), tmp_labels_dir)

    if os.path.exists(depth_src_path):
        move_files(depth_src_path, tmp_depth_dir)
    
    shuffle_and_rename(tmp_dir, src_dir, baseIdx, name_type)
    shutil.rmtree(tmp_dir)
                
if __name__=='__main__':
    shuffle_and_rename_local(r'D:\data\mergedir-1')