import os
import shutil
import numpy as np
import xml.etree.ElementTree as ET
from libs.xml_io import voc_main_txt_generator as voc_generator
from libs.dir_and_filename_info import *
from libs import voc_data_checker

jpgDir = "JPEGImages"
xmlDir = "Annotations"
txtDir = "ImageSets/Main"

def get_label_to_filenames(annots):
    label_to_filenames = {}
    idx = 0
    for annot in annots:
        idx += 1
        et = ET.parse(annot)
        element = et.getroot()
        element_objs = element.findall('object')
        element_filename = element.find('filename').text

        if len(element_objs) == 0:
            if 'unknown' not in label_to_filenames:
                label_to_filenames['unknown'] = []
            if element_filename not in label_to_filenames['unknown']:
                label_to_filenames['unknown'].append(element_filename)
        else:
            for element_obj in element_objs:
                label = element_obj.find('name').text
                if label not in label_to_filenames:
                    label_to_filenames[label] = []
                if element_filename not in  label_to_filenames[label]:
                    label_to_filenames[label].append(element_filename)


    return label_to_filenames

class FormatToVOCData:
    def __init__(self, dirpath, train_test_ratio, train_val_ratio, pos_neg_ratio):
        self.dirpath = dirpath
        self.jpgpath = os.path.join(self.dirpath, jpgDir)
        self.xmlpath = os.path.join(self.dirpath, xmlDir)
        self.txtpath = os.path.join(self.dirpath, txtDir)
        self.train_test_ratio = train_test_ratio
        self.train_val_ratio = train_val_ratio
        self.pos_neg_ratio = pos_neg_ratio
            
    def start_format(self):
        if not os.path.isdir(self.jpgpath):
            os.mkdir(self.jpgpath)
        if not os.path.isdir(self.xmlpath):
            os.mkdir(self.xmlpath)
        if not os.path.isdir(self.txtpath):
            os.makedirs(self.txtpath)

        label_to_num = voc_data_checker.get_label_info(self.dirpath)
        print('label_to_num', label_to_num)
        with open(os.path.join(self.dirpath, 'labels.txt'), 'w+') as label_file:
            for label in label_to_num:
                label_file.write('%s\n' % label)

        image_exist_path = find_images_exist_path(self.dirpath)
        label_exist_path = find_labels_exist_path(self.dirpath)
        img_files = os.listdir(image_exist_path)
        for file in img_files:
            if file.endswith(".jpg"):
                shutil.move(os.path.join(image_exist_path, file), os.path.join(self.jpgpath, file))

        xml_files = os.listdir(label_exist_path)
        for file in xml_files:
            if file.endswith(".xml"):
                shutil.move(os.path.join(label_exist_path, file), os.path.join(self.xmlpath, file))
                
        self.generate_txt_files()
        print('format voc done')
  
    def generate_txt_files(self):
        trainvaltext_path = os.path.join(self.txtpath,'trainval.txt')
        testtext_path = os.path.join(self.txtpath,'test.txt')

        annots = [os.path.join(self.xmlpath,s) for s in os.listdir(self.xmlpath)]
        
        #get train and test filenames
        xmlNames = os.listdir(self.xmlpath)

        trainval_filenames = np.random.choice(xmlNames, int(len(xmlNames)*self.train_test_ratio),replace = False)
        test_filenames = []
        for file in xmlNames:
            if file not in trainval_filenames:
                test_filenames.append(file)
                
        voc_generator.write_sample_name_to_file(trainvaltext_path,trainval_filenames)
        voc_generator.write_sample_name_to_file(testtext_path,test_filenames)

        # get each label, and list of the sample that contain the label
        label_to_filenames = get_label_to_filenames(annots)

        # get train positive sample ,train negative sample ,validation positive sample validation negative sample  
        train_pos_filenames = {}
        train_neg_filenames = {}
        val_pos_filenames = {}
        val_neg_filenames = {}
        # print('label to filenames', label_to_filenames)
        # print('trainval filenames', trainval_filenames)
        for label in label_to_filenames:
            trainval_pos_filenames, trainval_neg_filenames = voc_generator.get_class_pos_neg_filenames(label_to_filenames[label], trainval_filenames)

            # print('trainval_pos_filenames', trainval_pos_filenames)
            # print('trainval_neg_filenames', trainval_neg_filenames)
            test_pos_filenames, test_neg_filenames = voc_generator.get_class_pos_neg_filenames(label_to_filenames[label], test_filenames)
            train_pos_filenames[label], val_pos_filenames[label] = voc_generator.get_train_val_pos_sample_filenames(trainval_pos_filenames, self.train_val_ratio)

            num_train = int((len(train_pos_filenames[label]) /self.pos_neg_ratio))
            if num_train > len(train_pos_filenames) + len(trainval_neg_filenames):
                num_train_neg = len(trainval_neg_filenames)
            else:
                num_train_neg = num_train - len(train_pos_filenames)

            train_neg_filenames[label], val_neg_filenames[label] = voc_generator.get_train_val_neg_sample_filenames(trainval_neg_filenames, num_train_neg)

        for label in label_to_filenames:
            imgsets_path_class_trainval = os.path.join(self.txtpath, label + '_trainval.txt')
            imgsets_path_class_train = os.path.join(self.txtpath, label + '_train.txt')
            imgsets_path_class_val = os.path.join(self.txtpath, label + '_val.txt')
    
            fclass_trainval = open(imgsets_path_class_trainval,'w')
            voc_generator.write_sample_to_file(imgsets_path_class_trainval, train_pos_filenames[label], '1')
            voc_generator.write_sample_to_file(imgsets_path_class_trainval, train_neg_filenames[label], '-1')
            voc_generator.write_sample_to_file(imgsets_path_class_trainval, val_pos_filenames[label], '1')
            voc_generator.write_sample_to_file(imgsets_path_class_trainval, val_neg_filenames[label], '-1')
            fclass_trainval.close()
     
            fclass_train = open(imgsets_path_class_train,'w')
            voc_generator.write_sample_to_file(imgsets_path_class_train, train_pos_filenames[label], '1')
            voc_generator.write_sample_to_file(imgsets_path_class_train, train_neg_filenames[label], '-1')
            fclass_train.close()
    
            fclass_val = open(imgsets_path_class_val,'w')
            voc_generator.write_sample_to_file(imgsets_path_class_val, val_pos_filenames[label], '1')
            voc_generator.write_sample_to_file(imgsets_path_class_val, val_neg_filenames[label], '-1')
            fclass_val.close()
        
             
    