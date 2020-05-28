from generate_data.ItemProcessor import ItemProcessor
import logging

class UpdateGenerateNum(ItemProcessor):
    type = 'GenStopCond'
    inputs = {'items', 'label_to_density_gennum'}
    outputs = ['_label_to_item_count']

    def __init__(self,  **kwargs):
        super().__init__(**kwargs)

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ' + self.type + ' require:', self.inputs, 'real:',
                            key_to_inputs.keys())
        _label_to_density_gennum = key_to_inputs['label_to_density_gennum']
        _items = key_to_inputs['items']
        _label_to_item_count = {}
        for _item in _items:
            if _item.is_contain_sub_items():
                for sub_item in _item.sub_items:
                    if sub_item.is_covered:
                        continue
                    if _item.name in _label_to_item_count.keys():
                        _label_to_item_count[_item.name] += 1
                    else:
                        _label_to_item_count[_item.name] = 1
            else:
                if _item.is_covered:
                    continue
                if _item.name in _label_to_item_count.keys():
                    _label_to_item_count[_item.name] += 1
                else:
                    _label_to_item_count[_item.name] = 1
        return[_label_to_item_count]
