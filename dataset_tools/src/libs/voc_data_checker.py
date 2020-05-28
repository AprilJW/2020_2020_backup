import os
import logging
from tqdm import tqdm
from libs.xml_io import xml_editor
from libs.dir_and_filename_info import *
from libs.json_io import json_parser_io
def get_label_info(dir_path):
    """
        trace path for voc style xml, count each labels
        Args
            dir_path:
        Return:
             dict of label:count
    """
    
    labels_exist_path = find_labels_exist_path(dir_path)
    label_files = os.listdir(labels_exist_path)
    label_to_num = {}
    for file_name in tqdm(label_files, "check label:"):
        file_name_split = os.path.splitext(file_name)
        if file_name_split[1] == ".xml":
            xml_path = os.path.join(labels_exist_path, file_name)
            tree = xml_editor.read_xml(xml_path)
            nodes = xml_editor.find_nodes(tree, "object/name")
            for node in nodes:
                if node.text not in label_to_num:
                    label_to_num.setdefault(node.text,1)
                else:
                    label_to_num[node.text] += 1

        if file_name_split[1] == ".json":
            # Method1
            json_reader = json_parser_io.JsonParserIO.from_file(os.path.join(labels_exist_path, file_name))
            if len(json_reader.objects) == 0:
                continue
            for obj in json_reader.objects:
                if obj.label not in label_to_num:
                    label_to_num.setdefault(obj.label,1)
                else:
                    label_to_num[obj.label] += 1
            
    return label_to_num

def get_exist_labels(label_file):
    labels = []
    if os.path.splitext(label_file)[1] == '.xml':
        tree = xml_editor.read_xml(label_file)
        nodes = xml_editor.find_nodes(tree, "object/name")
        for node in nodes:
            labels.append(node.text)
            
    elif os.path.splitext(label_file)[1] == '.json':
        json_reader = json_parser_io.JsonParserIO.from_file(label_file)
        for obj in json_reader.objects:
            labels.append(obj.label)
    
    return labels
        

def rename_label(dir_path, old_to_new_label):
    labels_exist_path = find_labels_exist_path(dir_path)
    files = os.listdir(labels_exist_path)
    for file_name in tqdm(files, "rename label"):
        file_name_split = os.path.splitext(file_name)
        label_path = os.path.join(labels_exist_path , file_name)
        exist_labels = get_exist_labels(label_path)
        old_to_new_label_filtered = dict([(label, old_to_new_label[label]) for label in exist_labels])
        
        if file_name_split[1] == ".xml":
            tree = xml_editor.read_xml(label_path)
            for label in old_to_new_label_filtered:
                update_xml_info(tree, "object/name", label, old_to_new_label[label], True)
            xml_editor.write_xml(tree, label_path)
        elif file_name_split[1] == ".json":
            json_reader = json_parser_io.JsonParserIO.from_file(label_path)
            for json_label in old_to_new_label_filtered:
                update_json_info(json_reader, json_label, old_to_new_label[json_label])
            json_parser_io.write_json(json_reader,label_path)
        else:
            pass


def _rename_sub_files(sub_root_path, old_name, new_name, ext):
    sub_path = os.path.join(sub_root_path, old_name + ext)
    if os.path.isfile(sub_path):
        new_pickle_name = os.path.join(sub_root_path, new_name + ext)
        os.rename(sub_path, new_pickle_name)


def rename_jpg_files(dir_path, prefix, idx=0, zero_fill=6):
    images_exist_path = find_images_exist_path(dir_path)
    labels_exist_path = find_labels_exist_path(dir_path)
    depth_exist_path = find_depth_exist_path(dir_path)
    
    depth_list = os.listdir(depth_exist_path) if depth_exist_path else None
    depth_suffix = ""
    if depth_list:
        depth_suffix = os.path.splitext(depth_list[0])[-1]
        
    jpg_files = get_sorted_file_name_list(images_exist_path)
    zero_fill_num = zero_fill if prefix.startswith('2007_') else -1
    for jpg_file in tqdm(jpg_files, "rename files: "):
        old_path = os.path.join(images_exist_path, jpg_file)
        file_name_split = os.path.splitext(jpg_file)
        folder_path = os.path.split(images_exist_path)[-1]
        if file_name_split[1] in img_extensions:
            new_name = "_rename_" + get_file_name(idx=idx, prefix=prefix, zfill=zero_fill_num, suffix=file_name_split[1],)
            new_path = os.path.join(images_exist_path, new_name)
            os.rename(old_path, new_path)
            idx += 1
            # check if need rename xml node
            xml_path = os.path.join(labels_exist_path, file_name_split[0] + ".xml")
            if os.path.isfile(xml_path):
                tree = xml_editor.read_xml(xml_path)
                update_xml_info(tree, "filename", "", new_name[8:], False)
                update_xml_info(tree, "path", "", new_path, False)
                update_xml_info(tree, "folder", "", folder_path, False)
                
                new_xml_path = os.path.join(labels_exist_path, os.path.splitext(new_name)[0] + '.xml')
                xml_editor.write_xml(tree, xml_path)
                os.rename(xml_path, new_xml_path)
            else:
                logging.info("rename jpg file but not has xml file")

            new_name_no_ext = os.path.splitext(new_name)[0]
            
            if depth_exist_path:
                _rename_sub_files(depth_exist_path, file_name_split[0], new_name_no_ext, depth_suffix)

            _rename_sub_files(labels_exist_path, file_name_split[0], new_name_no_ext, '.json')

    for file_dir in [images_exist_path, labels_exist_path, depth_exist_path]:
        if not file_dir or not os.path.isdir(file_dir) or not os.listdir(file_dir):
            continue
        for file_name in os.listdir(file_dir):
            new_file_name = file_name[8:]
            os.rename(os.path.join(file_dir,file_name),os.path.join(file_dir, new_file_name))
    logging.info('rename jpg done')
    return idx


def merge_data_set(src_paths, dest_path, start_index=0, prefix="2007_", is_change_src_file=True):
    idx = start_index
    make_data_dirs(dest_path=dest_path)
    idx = rename_jpg_files(dir_path=dest_path, prefix=prefix, idx=idx)
    for src_path in src_paths:
        logging.info('src_path:'+src_path)
        idx = rename_jpg_files(dir_path=src_path, prefix=prefix,idx=idx)
        for sub_dir in sub_dirs:
            merge_two_dirs(src_path=os.path.join(src_path,sub_dir),dest_path=os.path.join(dest_path,sub_dir))
            

def update_xml_info(tree, node_name, old_value, new_value, is_condition):
    if old_value == new_value:
        return
    text_nodes = xml_editor.find_nodes(tree, node_name)

    if is_condition:
        xml_editor.change_node_text_with_condition(text_nodes, old_value, new_value)
    else:
        xml_editor.change_node_text(text_nodes, new_value)

def update_json_info(json_reader, old_value, new_value):
    if old_value == new_value:
        return
    for obj in json_reader.objects:
        if obj.label == old_value:
            obj.label = new_value

def check_data(dir_path):
    src_images_path = find_images_exist_path(dir_path)
    src_labels_path = find_labels_exist_path(dir_path)
    files = os.listdir(src_images_path)
    for file in files:
        file_name_split = os.path.splitext(file)
        if file_name_split[1] == ".jpg":
            xml_path = os.path.join(src_labels_path, file_name_split[0],".xml")
            if not os.path.isfile(xml_path):
                # shutil.move(os.path.join(dirpath, file), "d:")
                logging.info("xml file not exist:" + xml_path)

    files = os.listdir(src_labels_path)
    for file in files:
        file_name_split = os.path.splitext(file)
        if file_name_split[1] == ".xml":
            jpg_path = os.path.join(src_images_path, file_name_split[0], ".jpg")
            if not os.path.isfile(jpg_path):
                # shutil.move(os.path.join(dirpath, file), "d:")
                print("jpg file not exist:" + jpg_path)

if __name__ == '__main__':
    dest_path = "/home/amax/Deep_learning_weights_and_data/train_data/results/20180411_jd_cosmetics_eachsurface"
    src = "/home/amax/Deep_learning_weights_and_data/train_data/results/20180411_jd_cosmetics_eachsurface/config1"
    src_paths = os.listdir(src)
    src_paths = [os.path.join(src,sub_path) for sub_path in src_paths]
    merge_data_set(src_paths=src_paths,dest_path=dest_path)
