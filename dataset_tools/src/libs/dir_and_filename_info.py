import os
import sys
import uuid
import json
import shutil
from PyQt5.Qt import QMessageBox

VOC, RGB = range(2)

img_extensions = ['.jpeg', '.jpg', '.bmp']
depth_extensions = ['.png', '.exr']
label_extensions = ['.json', '.xml', '.pickle']


def get_file_name(idx=0, prefix='2007_', zfill=-1, suffix=''):
    if zfill == -1:
        return prefix + str(idx) + suffix
    else:
        return prefix + str(idx).zfill(zfill) + suffix


voc_prefix = '2007_'
rgb_prefix = 'rgb_image_'


def voc_name(idx):
    return get_file_name(idx, voc_prefix, 6)


def rgb_image_name(idx):
    return get_file_name(idx, rgb_prefix)


def uuid_name():
    return str(uuid.uuid4())


DIR_IMAGES = 'images'
DIR_LABELS = 'labels'
DIR_DEPTH = 'depth_images'
DIR_DEPTH_ENCODED = 'depth_images_encoded'
DIR_MASK = 'SegmentationClass'
DIR_VALIDATION = "validation"

XML_TYPE_VERTEX = "Vertexs(Mask)"
XML_TYPE_BNDBOX = "Bndbox(Detection)"
XML_TYPE_MIX = "Mix"

RESIZE_MODE_CROP = "Crop"
RESIZE_MODE_FILL = "Auto Fill"
RESIZE_MODE_PLAIN = "Maintain H/W Ratio"
RESIZE_MODE_ROI = "ROI"
RESIZE_MODE_FILE = "FILE"

EXT_XML = '.xml'
EXT_JSON = '.json'

sub_dirs = [DIR_IMAGES, DIR_LABELS]


def get_dir_file_list(src_path):
    children = os.listdir(src_path)
    dir_list = []
    file_list = []
    for child in children:
        sub_path = os.path.join(src_path, child)
        if os.path.isdir(sub_path):
            dir_list.append(child)
        elif os.path.isfile(sub_path):
            file_list.append(child)
    return dir_list, file_list


# get file name("rgb_image_0.jpg"), sorted by index
def get_sorted_file_name_list(dir_path):
    _, file_list = get_dir_file_list(dir_path)
    file_list.sort(key=lambda x: int(x.split('.')[0].split('_')[-1]))
    return file_list

# get dir path that need to be, if not exist "images" dir, can create one if need


def get_dir_path(dest_path, sub_dir, create_if_not_exist=False):
    dir_path = os.path.join(dest_path, sub_dir)
    if create_if_not_exist:
        os.makedirs(dir_path, exist_ok=True)
    return dir_path

# find path where *.jps, *.xml, *.json, etc. actually exists


def find_images_exist_path(dir_path):
    return os.path.join(dir_path, DIR_IMAGES) if is_images_path_exist(dir_path) else dir_path


def find_labels_exist_path(dir_path):
    return os.path.join(dir_path, DIR_LABELS) if is_labels_path_exist(dir_path) else dir_path


def find_depth_exist_path(dir_path):
    depth_path = os.path.join(dir_path, DIR_DEPTH)
    return depth_path if os.path.exists(depth_path) else None


def get_label_file_path(dir_path, image_file_name, label_type='.xml'):
    if is_images_path_exist(dir_path):
        return os.path.join(dir_path, DIR_LABELS, os.path.splitext(image_file_name)[0] + label_type)
    else:
        return os.path.join(dir_path, os.path.splitext(image_file_name)[0] + label_type)


def is_image_file(file):
    return file.endswith(tuple(img_extensions))


def is_label_file(file):
    return file.endswith(tuple(label_extensions))


def is_images_path_exist(dir_path):
    return os.path.exists(os.path.join(dir_path, DIR_IMAGES))

def is_depth_path_exist(dir_path):
    return os.path.exists(os.path.join(dir_path, DIR_DEPTH))

def is_labels_path_exist(dir_path):
    return os.path.exists(os.path.join(dir_path, DIR_LABELS))

def is_label_file_exist(dir_path, img_full_path):
    file_name = os.path.splitext(os.path.basename(img_full_path))[0]
    for label_ext in label_extensions:
        label_file_name = file_name + label_ext
        label_full_path = os.path.join(find_labels_exist_path(dir_path), label_file_name)
        if os.path.isfile(label_full_path):
            return True, label_full_path
    return False, None


# to judge if images labels mixed or images depth mixed
def is_images_labels_depth_mixed(dir_path):
    label_exist = False
    image_exist = False
    depth_exist = False
    for file in os.listdir(dir_path):
        extension = os.path.splitext(file)
        if extension[1] in label_extensions:
            label_exist = True
        if extension[1] in img_extensions:
            image_exist = True
        if extension[1] in depth_extensions:
            depth_exist = True
        if (label_exist and image_exist) or (image_exist and depth_exist):
            return True
    return False


def is_coco_dataset(dir_path):
    if ((os.path.exists(os.path.join(dir_path, 'train2014'))) or (os.path.exists(os.path.join(dir_path, 'val2014')))) \
            and (os.path.exists(os.path.join(dir_path, 'annotations'))):
        return True
    return False


def is_voc_dataset(dir_path):
    if ((os.path.exists(os.path.join(dir_path, 'JPEGImages'))) and (
            os.path.exists(os.path.join(dir_path, 'SegmentationClass')))):
        return True
    return False


def move_files(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            relatviePath = os.path.join(root, file)
            path = os.path.abspath(relatviePath)
            shutil.move(path, os.path.join(dest_dir, file))

# for jpgs and xmls/jsons in one dir, copy jpgs to "images" dir, label file to "labels" dir


def split_dir_to_images_labels(dir_path):
    images_dest_path = get_dir_path(dir_path, DIR_IMAGES, create_if_not_exist=True)
    depth_dest_path = get_dir_path(dir_path, DIR_DEPTH, create_if_not_exist=True)
    labels_dest_path = get_dir_path(dir_path, DIR_LABELS, create_if_not_exist=True)

    files = os.listdir(dir_path)
    for file in files:
        relativePath = os.path.join(dir_path, file)
        path = os.path.abspath(relativePath)
        if os.path.isfile(path):
            if file.lower().endswith(tuple(depth_extensions)):
                shutil.move(path, os.path.join(depth_dest_path, file))
                continue
            if file.lower().endswith(tuple(img_extensions)):
                shutil.move(path, os.path.join(images_dest_path, file))
            if file.lower().endswith(tuple(label_extensions)):
                shutil.move(path, os.path.join(labels_dest_path, file))
    
    depth_list = os.listdir(depth_dest_path)
    if depth_list and depth_list[0].startswith("depth"):
        depth_suffix = os.path.splitext(depth_list[0])[-1]
        for depth_name in depth_list:
            os.rename(os.path.join(depth_dest_path,depth_name),
                      os.path.join(depth_dest_path,"rgb_image_" + os.path.splitext(depth_name)[0].split("_")[-1] + depth_suffix))

# merge files in "images" and "labels" dir to one dir


def merge_images_labels_to_one_dir(dir_path):
    if not is_images_path_exist(dir_path) or not is_labels_path_exist(dir_path):
        QMessageBox.warning(None, 'warning', 'No images or labels exist')

    images_path = os.path.join(dir_path, DIR_IMAGES)
    labels_path = os.path.join(dir_path, DIR_LABELS)
    move_files(images_path, dir_path)
    move_files(labels_path, dir_path)
    os.rmdir(images_path)
    os.rmdir(labels_path)


def write_file_list(dir_path, file_name_list):
    with open(os.path.join(dir_path, 'file_list.txt'), 'a+') as f:
        for file_name in file_name_list:
            content_line = os.path.splitext(os.path.basename(file_name))[0] + '\n'
            f.write(content_line)
    QMessageBox.information(None, 'Info', "write file list to " + dir_path + '/file_list.txt')


def make_data_dirs(config_key="", dest_path="D:/"):
    print(config_key, dest_path)

    os.makedirs(os.path.join(dest_path, config_key), exist_ok=True)
    for sub_dir in sub_dirs:
        os.makedirs(os.path.join(dest_path, config_key, sub_dir), exist_ok=True)


def merge_two_dirs(src_path, dest_path):
    if os.path.isdir(src_path):
        files = os.listdir(src_path)
        for file_name in files:
            src_file = os.path.join(src_path, file_name)
            dest_file = os.path.join(dest_path, file_name)
            shutil.copy(src_file, dest_file)


def read_json_config_file(config_path):
    param = None
    if config_path is not None and os.path.exists(config_path):
        try:
            config_file = open(config_path, 'r')
            _data = config_file.read()
            param = json.loads(_data)
        except BaseException:
            print("json.load", sys.exc_info()[0])
    return param


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def get_all_images_xmls(src_path):
    file_names = os.listdir(src_path)
    # trace folder searching xml for ROI info
    img_full_paths = []
    xml_full_paths = []
    for filename in file_names:
        file_name_split = os.path.splitext(filename)
        if file_name_split[1] in ['.jpg', '.bmp', '.png']:
            img_full_paths.append(os.path.join(src_path, filename))
            xml_full_path = os.path.join(src_path, file_name_split[0] + '.xml')
            if os.path.isfile(xml_full_path):
                xml_full_paths.append(xml_full_path)

    return img_full_paths, xml_full_paths

def get_file_ext(src_path):
    if src_path:
        files = os.listdir(src_path)
        if files:
            return os.path.splitext(files[0])[1]
    return ""


class dir_parser:
    
    def __init__(self, src_dir, dst_dir):
        
        if not is_images_path_exist(src_dir) or not is_labels_path_exist(src_dir):
            split_dir_to_images_labels(src_dir)
            
        self.src_image_dir = find_images_exist_path(src_dir)
        self.src_label_dir = find_labels_exist_path(src_dir)
        self.src_depth_dir = find_depth_exist_path(src_dir)
        
        self.image_ext = get_file_ext(self.src_image_dir)
        self.label_ext = get_file_ext(self.src_label_dir)
        self.depth_ext = get_file_ext(self.src_depth_dir)

        self.dst_image_dir = os.path.normpath(get_dir_path(dst_dir, DIR_IMAGES, True))
        self.dst_label_dir = os.path.normpath(get_dir_path(dst_dir, DIR_LABELS, True))
        self.dst_depth_dir = os.path.normpath(get_dir_path(dst_dir, DIR_DEPTH, True)) if self.src_depth_dir else None
        

    def get_src_files_by_name(self, data_name):
        return os.path.join(self.src_image_dir, data_name + self.image_ext), \
            os.path.join(self.src_label_dir, data_name + self.label_ext), \
            os.path.join(self.src_depth_dir, data_name + self.depth_ext) if self.src_depth_dir else None
    
    def get_dst_files_by_name(self, data_name):
        return os.path.join(self.dst_image_dir, data_name + self.image_ext), \
            os.path.join(self.dst_label_dir, data_name + self.label_ext), \
            os.path.join(self.dst_depth_dir, data_name + self.depth_ext) if self.src_depth_dir else None
    
    def all_data_names(self):
        return [os.path.splitext(f)[0] for f in sorted(os.listdir(self.src_image_dir))]
