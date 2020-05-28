import os
import subprocess

from train_predict.ModelTypeEnum import ModelTypeEnum

class PredictHelper:
    def __init__(self, model_type, weight_path, data_path):
        self.model_type = model_type
        self.data_path = data_path
        self.weight_path = weight_path

    def start_predicting(self):
        arg = self._get_predict_cmd(self.model_type)
        subprocess.Popen(arg, shell=True)

    def calculate_mAP(self):
        arg = _get_calculate_mAP_cmd(os.path.abspath("../../Faster-RCNN-Keras/src/measure_map.py"), self.weight_path,
                               self.data_path)
        child = subprocess.Popen(arg, shell=True)
        child.communicate()
        mAP = child.returncode
        print('return code', mAP)
        return mAP

    def _get_predict_cmd(self, model_type):
        if not model_type.strip():
            return None
        if model_type == ModelTypeEnum.Retina.name:
            script = os.path.abspath('../../RetinaNet/keras_retinanet/bin/inference.py')
            return self._get_Retina_predict_cmd(script, self.weight_path, self.data_path)
        if model_type == ModelTypeEnum.FRCNN.name:
            script = os.path.abspath('../../Faster-RCNN-Keras/src/test_frcnn.py')
            return self._get_FRCNN_predict_cmd(script, self.weight_path, self.data_path)

    def _get_Retina_predict_cmd(self, script, weight_path, data_path):
        arg = 'python' + ' ' + script
        arg += ' ' + '-p' + ' ' + data_path
        arg += ' ' + '--model_path' + ' ' + os.path.join(weight_path, 'resnet50_pascal_16_inference.h5')
        arg += ' ' + '--class_path' + ' ' + os.path.join(weight_path, 'class.json')
        return arg

    def _get_FRCNN_predict_cmd(self, script, weight_path, data_path):
        arg = 'python' + ' ' + script
        arg += ' ' + '-p' + ' ' + data_path
        arg += ' ' + '--model_path' + ' ' + os.path.join(weight_path, 'model_frcnn.hdf5')
        arg += ' ' + '--config_filename' + ' ' + os.path.join(weight_path, 'config.pickle')
        return arg


def _get_calculate_mAP_cmd(script, model_path, data_path):
    arg = 'python' + ' ' + script
    arg += ' ' + '-p' + ' ' + os.path.dirname(data_path)
    arg += ' ' + '--data_name' + ' ' + os.path.basename(data_path)
    arg += ' ' + '--model_path' + ' ' + os.path.join(model_path, 'model_frcnn.hdf5')
    arg += ' ' + '--config_filename' + ' ' + os.path.join(model_path, 'config.pickle')
    return arg

# import cv2
# import time
# import numpy as np
# from xml_io import pascal_voc_io
# from predictor.detector.frcnn import frcnnPredictor
# 
# def save_predict_to_xml(srcPath, modelPath):
#     filenames = os.listdir(srcPath)
#     predictor = PredictHelper(modelPath)
#     for filename in filenames:
#         filenamesplit = os.path.splitext(filename)
#         if filenamesplit[1] != '.jpg':
#             continue
#             
#         file_fullpath = os.path.join(srcPath, filename)
#         predictor.start_predict(file_fullpath)


#             
# class PredictHelper:
#     def __init__(self, model_path = '../'):
#         self.predictor = frcnnPredictor(os.path.join(model_path, "model_frcnn.hdf5"), os.path.join(model_path, "config.pickle"))
#         
#     def start_predict(self, img_path):
#         imgFolderPath = os.path.dirname(img_path)
#         folderName = os.path.split(imgFolderPath)[-1]
#         imgFileName = os.path.basename(img_path)
#         
#         img = cv2.imread(img_path)
#         shape = img.shape
#         
#         #start predict
#         result = self.predictor.predict(img)
# 
#         size = len(result)
#         if size < 0:
#             return None
#         
#         #save result to xml file
#         bndBoxs = []
#         for i in range(size):    
#             label= result[i][0]
#             xmin = result[i][2][0]
#             ymin = result[i][2][1]
#             xmax = result[i][2][2] + xmin
#             ymax = result[i][2][3] + ymin
#             confidence = result[i][1]
#             bndBox = [int(xmin), int(ymin), int(xmax), int(ymax), str(label), float(confidence)]
#             bndBoxs.append(bndBox)
#             
#         pw = pascal_voc_io.PascalVocWriter(folderName, imgFileName, shape, localImgPath=img_path)
#         for bndBox in bndBoxs:
#             pw.addBndBox(int(bndBox[0]), int(bndBox[1]), int(bndBox[2]), int(bndBox[3]), bndBox[4], bndBox[5])
#         
#         xmlPath = os.path.splitext(img_path)[0] + '.xml'
#         pw.save(xmlPath)
#     
#              
#     