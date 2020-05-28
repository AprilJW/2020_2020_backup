import xml.etree.ElementTree as ET
import numpy as np
import os
import shutil
""" generate each class samples file name,with"""

# get each class 
def get_classes_filename(annots):
    classes_count = {}
    classes_files = {}
    idx = 0
    for annot in annots:
        try:
            idx += 1
            et = ET.parse(annot)
            element = et.getroot()
            element_objs = element.findall('object')
            element_filename = element.find('filename').text
            
            for element_obj in element_objs:
                classes_filenamelist=[]
                class_name = element_obj.find('name').text
                if class_name not in classes_count:
                    classes_count[class_name] = 1
                    classes_filenamelist.append(element_filename)
                else:
                    classes_count[class_name] += 1
                    classes_filenamelist = classes_files[class_name]
                    classes_filenamelist.append(element_filename)
                    
                classes_files[class_name] = classes_filenamelist
                
        except Exception as e:
            print('Exception: {}'.format(e))
    
    return classes_count,classes_files

def get_class_pos_neg_filenames(class_jpg_files, label_files):
    class_pos_filenames = []
    class_neg_filenames = []
    # print('class jpg files', class_jpg_files)
    for xml_file in label_files:
        filename, ext = os.path.splitext(xml_file)
        jpg_file = filename + '.jpg'
        if jpg_file in class_jpg_files:
            class_pos_filenames.append(jpg_file)
        else:
            class_neg_filenames.append(jpg_file)
            
    return class_pos_filenames, class_neg_filenames

def get_class_trainval_neg_filenames(classes_files,class_name, num_trainval_neg_sample):
    neg_samples = []
    for classes in classes_files:
        if classes != class_name:
            neg_samples.extend(classes_files[classes])
    neg_samples = list(set(neg_samples))
    #print(len(neg_samples),num_trainval_neg_sample)
    # print('neg samples', neg_samples)
    # print('num', num_trainval_neg_sample)
    if len(neg_samples) == 0:
        return []
    neg_trainval_samples = np.random.choice(neg_samples, num_trainval_neg_sample,replace = False).tolist()
    
    return neg_trainval_samples


def get_train_val_pos_sample_filenames(pos_sample_filenames, radio_train_val_pos):
    # print('pos sample filenames', pos_sample_filenames)
    if len(pos_sample_filenames) == 0:
        return [], []
    train_pos_samples = np.random.choice(pos_sample_filenames,int(len(pos_sample_filenames)*radio_train_val_pos),replace = False).tolist()
    val_pos_samples = []
    for sample in pos_sample_filenames:
        if sample not in train_pos_samples:
            val_pos_samples.append(sample)
    return train_pos_samples,val_pos_samples

def get_train_val_neg_sample_filenames(neg_sample_filenames, num_train_neg_sample):
    if len(neg_sample_filenames) == 0:
        return [], []
    neg_train_sample_filenames = np.random.choice(neg_sample_filenames,num_train_neg_sample,replace = False).tolist()
    neg_val_sample_filenames = []
    for sample in neg_sample_filenames:
        if sample not in neg_train_sample_filenames:
            neg_val_sample_filenames.append(sample)
    return neg_train_sample_filenames,neg_val_sample_filenames

def write_sample_name_to_file(file_name,samples):
    files = open(file_name,'w')
    for sample in samples:
        files.write(sample[0:-4]+'\n')
    files.close()

def write_sample_to_file(file_name,samples,label):
    files = open(file_name,'a+')
    for sample in samples:
        files.write(sample[0:-4]+' '+label+'\n')
    files.close()
def write_sample_dict_to_file(file_name,samples):
    files = open(file_name,'a+')
    keys = sorted(samples.keys())
    
    for key in keys:
        files.write(key[0:-4] + ' '+ samples[key] + '\n')
    files.close()
    
def move_xml_to_annot(src_dir,target_dir):
    listFiles = os.listdir()
    for files in listFiles:
        filename,ext = os.path.splitext(files)
        filenameHead,filename = os.path.split(files)
        if ext == 'xml':
            shutil.copy2(files,os.path.join(target_dir,filename))

def rename_file_in_train(src_dir,target_dir,startIndex,ext):
    #get all file in dir
    files = os.listdir(src_dir)
    n=0
    import xml.etree.ElementTree as ET
    from _elementtree import Element
    for file in files:
    
        #old file name 
        oldname = src_dir + files[n]
    
        #make new file name
        newname = 'mech_'+str(startIndex)+'.jpg'
    
        #rename
        os.rename(oldname,newname)
        print(oldname,'======>',newname)
        n+=1
        startIndex += 1
            
            
        