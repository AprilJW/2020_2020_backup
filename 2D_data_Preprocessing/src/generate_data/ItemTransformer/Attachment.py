from generate_data import ItemProcessor
from util import item_algo


class Attachment(ItemProcessor.ItemProcessor):
    type = 'Attachment'
    inputs = {'item', 'attachments', 'attachemnt_list'}
    outputs = ['item']

    def __init__(self, shade_offset=-30, shade_scale=1):
        pass

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        for _item in _items:
            _item = item_algo.add_attachment(_item, self.inputs['attachments'], self.inputs['attachemnt_list'])
        return [_items]
