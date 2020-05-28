import sys
import os
import subprocess

from train_predict.ModelTypeEnum import ModelTypeEnum
from util import util

sys.path.append(os.path.abspath(os.path.expanduser('../../../dataset_tools/src')))
from libs.format_voc_data import FormatToVOCData


class TrainHelper:
    def __init__(self, model_type, data_path, weight_path="", epoch=100, check_period=80):
        self.model_type = model_type
        self.data_path = data_path
        self.weight_path = weight_path
        self.epoch = epoch
        self.check_period = check_period

    def start_predicting(self):
        arg = self._get_train_cmd(self.model_type)
        subprocess.Popen(arg, shell=True)

    def format_and_train(self, dest_path, train_test_ratio, train_val_ratio, pos_neg_ratio ):
        try:
            voc_formatter = FormatToVOCData(dest_path, train_test_ratio, train_val_ratio, pos_neg_ratio)
            voc_formatter.start_format()
        except:
            print("voc format error")

        param = util.read_json_config_file('../config.json')['training_param']

        if param is not None and param != {}:
            weight_path = os.path.abspath(os.path.expanduser(param['--input_weight_path']))
            arg = self._get_FRCNN_train_cmd(param['python'], param['--num_epochs'], param['--checkPeriod'], weight_path, dest_path)
            print('arg', arg)
            subprocess.Popen(arg,shell=True)

    def _get_train_cmd(self, model_type):
        if not model_type.strip():
            return None
        if model_type == ModelTypeEnum.Retina.name:
            script = os.path.abspath('../../RetinaNet/keras_retinanet/bin/train.py')
            steps = None
            epochs = None
            data_type_pascal = 'pascal'
            data_type_coco = 'coco'
            return self._get_Retina_train_cmd(script, steps, epochs, data_type_pascal, self.data_path)
        if model_type == ModelTypeEnum.FRCNN.name:
            #weight_path = os.path.abspath(os.path.expanduser('~/Deep_learning_weights_and_data/weights/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5'))
            script = os.path.abspath('../../Faster-RCNN-Keras/src/train_frcnn.py')
            return self._get_FRCNN_train_cmd(script, self.epoch, self.check_period, self.weight_path, self.data_path)

    def _get_FRCNN_train_cmd(self,script, epoch, check_period, weight_path, data_path):
        arg = 'python' + ' ' + script
        arg += ' ' + "--num_epochs " + epoch
        arg += ' ' + "--checkPeriod " + check_period
        arg += ' ' + "--input_weight_path " + weight_path
        train_data_path = os.path.dirname(data_path)
        arg += ' ' + '-p' + ' ' + train_data_path
        arg += ' ' + '--data_name' + ' ' + os.path.basename(data_path)
        model_path = os.path.join(os.path.dirname(train_data_path), 'train_result', os.path.basename(data_path))
        os.makedirs(model_path, exist_ok=True)
        arg += ' ' + '--output_path' + ' ' + model_path
        arg += ' ' + '--output_weight_path' + ' ' + os.path.join(model_path, 'model_frcnn.hdf5')
        arg += ' ' + '--config_filename' + ' ' + os.path.join(model_path, 'config.pickle')
        return arg

    def _get_Retina_train_cmd(self, script, steps, epochs, data_type, weight_path, data_path):

        arg = 'python' + ' ' + script
        if steps:
            arg += ' ' + '--steps ' + str(steps)
        if epochs:
            arg += ' ' + '--epochs ' + str(epochs)
        if weight_path:
            arg += ' ' + '--weights ' + weight_path
        arg += ' ' + data_type
        arg += ' ' + data_path
        return arg

if __name__ == '__main__':
    train_helper = TrainHelper('Retina', 'a', 'b', 20, 20)
    print(train_helper._get_Retina_train_cmd(os.path.abspath('../../RetinaNet/keras_retinanet/bin/train.py'), 1000, 80, 'voc', 'd:/data/a/b'))