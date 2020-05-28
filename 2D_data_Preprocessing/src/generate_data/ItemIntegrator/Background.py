import os
import numpy as np
import cv2
from util import img_process_util
from generate_data.ItemProcessor import ItemProcessor
from ui.property.ProcessorProperty import DirPath


class ColorBackground(ItemProcessor):
    type = 'color_bg'
    outputs = ['background']

    def __init__(self, r=0, g=0, b=0, image_height=964, image_width=1292, **kwargs):
        super().__init__(**kwargs)
        self.r = r
        self.g = g
        self.b = b
        self.image_width = image_width
        self.image_height = image_height

    def process(self, key_to_input={}):
        background = np.zeros((self.image_height, self.image_width, 4), np.uint8)
        for ci, cr in enumerate([self.b, self.g, self.r]):
            background[:, :, ci] = cr
        return [background]


class RandomNoiseBackground(ItemProcessor):
    type = 'random_noise_bg'
    outputs = ['background']

    def __init__(self, image_height=964, image_width=1292, **kwargs):
        super().__init__(**kwargs)
        self.image_height = image_height
        self.image_width = image_width

    def process(self, key_to_inputs={}):
        if not self.is_used:
            return []
        background = img_process_util.random_noise_image(self.image_height, self.image_width)
        return [background]


class FileBackground(ItemProcessor):
    type = 'file_bg'
    outputs = ['background']

    def __init__(self, dir_path='', image_width=1292, image_height=964, b=0, g=0, r=0, **kwargs):
        super().__init__(**kwargs)
        if type(dir_path) is str:
            self.dir_path = DirPath(dir_path)
        elif type(dir_path) is DirPath:
            self.dir_path = dir_path
        else:
            raise TypeError('file background param type error expect:', type(DirPath), ' given ', type(dir_path))
        self.image_width = image_width
        self.image_height = image_height
        self.boarder_color_b = b
        self.boarder_color_g = g
        self.boarder_color_r = r

    def process(self, key_to_inputs={}):
        if not self.is_used:
            return []
        if not os.path.isdir(self.dir_path()):
            raise IsADirectoryError(self.dir_path())
        _files = os.listdir(self.dir_path())
        if not any(img_process_util.is_image_file(os.path.join(self.dir_path(), _file)) for _file in _files):
            raise ValueError('no image in file background dir')
        picked_file = _files[np.random.choice(len(_files), 1)[0]]
        while not img_process_util.is_image_file(os.path.join(self.dir_path(), picked_file)):
            picked_file = _files[np.random.choice(len(_files), 1)[0]]
        background = cv2.imread(os.path.join(self.dir_path(), picked_file))
        background = img_process_util.fit_image_to_size(img=background, target_width=self.image_width,
                                                        target_height=self.image_height,
                                                        fill_color=[self.boarder_color_b, self.boarder_color_g,
                                                                    self.boarder_color_r])
        b, g, r = cv2.split(background)
        alpha = np.zeros(b.shape, np.uint8)
        return [cv2.merge([b, g, r, alpha])]


if __name__ == '__main__':
    param = {'r': 100, 'g': 100, 'b': 100, 'image_height': 200, 'image_width': 300, 'is_used': False}
    opt = ColorBackground(**param)
    print(opt.is_used)

    opt = FileBackground(dir_path="d:/playground/Image/bg", image_height=500, image_width=500, b=100, g=50, r=150)
    imgs = opt.process()
    print('background end')
    cv2.imshow('background', imgs[0])
    cv2.waitKey(0)
    print(opt.dir_path())
