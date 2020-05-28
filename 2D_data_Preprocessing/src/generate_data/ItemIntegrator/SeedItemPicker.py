import copy
import numpy as np
import cv2
from generate_data.ItemProcessor import ItemProcessor
from util import item_algo
from util import img_process_util
import logging


class SeedItemPicker(ItemProcessor):
    type = 'SeedItemPicker'
    inputs = ['label_to_items', 'label_to_density_gennum', 'label_to_attachment', 'label_to_attachment_list']
    outputs = ['items', 'label_to_density_gennum']

    def __init__(self, is_norm_distribution=False, is_add_attachment=False, **kwargs):
        super().__init__(**kwargs)
        self.is_norm_distribution = is_norm_distribution
        self.is_add_attachment = is_add_attachment

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _label_to_items = key_to_inputs['label_to_items']
        _label_to_density_gennum = key_to_inputs['label_to_density_gennum']
        _label_to_attachment = key_to_inputs['label_to_attachment']
        _label_to_attachment_list = key_to_inputs['label_to_attachment_list']
        items = []
        _label_to_density_gennum_list = _label_to_density_gennum.items()
        if img_process_util.is_regression_test:
            _label_to_density_gennum_list = sorted(_label_to_density_gennum.items())
        for key, density_gennum in _label_to_density_gennum_list:
            if density_gennum['DensityMax'] == 0:
                continue
            if key in _label_to_items.keys():
                if self.is_norm_distribution:
                    density = max(int(np.ceil(np.random.normal(density_gennum['DensityMax'], 3, 1))), 1)
                    logging.info(str(density))
                else:
                    density = np.random.randint(density_gennum['DensityMin'], density_gennum['DensityMax'] + 1)
                    logging.info(str(density))
                _item_idx = np.random.choice(len(_label_to_items[key]), density).tolist()
                for idx in _item_idx:
                    items.append(copy.deepcopy(_label_to_items[key][idx]))
        np.random.shuffle(items)
        if self.is_add_attachment:
            for _item in items:
                _item = item_algo.add_attachment(_item, _label_to_attachment,
                                                 _label_to_attachment_list[_item.name])
        logging.info(str(_label_to_density_gennum))
        return [items, _label_to_density_gennum]
