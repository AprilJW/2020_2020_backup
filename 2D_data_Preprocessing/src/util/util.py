import os, shutil
import json

DIR_IMAGES = 'images'
DIR_LABELS = 'labels'

def tuple_to_list(tup):
    return [list(i) for i in tup]


def float_points_to_int(points):
    return [[int(point[0]), int(point[1])] for point in points]


def read_json_config_file(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


def merge_dir(src_path, dest_path):
    files = os.listdir(src_path)
    for file in files:
        src_file = src_path + "/" + file
        dest_file = dest_path + "/" + file
        shutil.copy(src_file, dest_file)


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


def get_str_file_name(idx=0, prefix='2007_', surfix='', zfill=6):
    str_file_name = str(idx)
    return prefix + str_file_name.zfill(6) + surfix


def get_expected_image_num(configs):
    expected_num = 0
    for key in configs:
        expected_num += configs[key].generate_image_num
    return expected_num


def check_image_num(dir_path, generate_image_num):
    image_path = os.path.join(dir_path, DIR_IMAGES)
    label_path = os.path.join(dir_path, DIR_LABELS)
    image_files = os.listdir(image_path)
    label_files = os.listdir(label_path)
    if len(image_files) == generate_image_num and len(label_files) == generate_image_num:
        return True , len(image_files)
    else:
        return False, len(image_files)

