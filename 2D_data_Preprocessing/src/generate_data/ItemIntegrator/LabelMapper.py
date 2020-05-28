import json
from generate_data.ItemProcessor import ItemProcessor
from ui.property.ProcessorProperty import FilePath

class LabelMapper(ItemProcessor):
    """update old_label to new_label by "label_mapper".json

    Attributes:
        file_path: Absolute path of "label_mapper".json

    """

    type = 'LabelMapper'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, file_path='', **kwargs):
        super().__init__(**kwargs)
        if type(file_path) is str:
            self.file_path = FilePath(file_path)
        elif type(file_path) is FilePath:
            self.file_path = file_path
        else:
            raise TypeError('label mapper file type error:', type(FilePath), ' given ', type(file_path))
        self.old_to_new = {}
        self.old_to_new = self.load_if_needed(self.old_to_new, self.file_path())
        self.not_display.append("old_to_new")

    def load_if_needed(self, json_obj, file_path):
        if not json_obj and file_path.strip():
            with open(file_path, 'r') as f:
                json_obj = json.load(f)
        return json_obj

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        if _items is None:
            return None
        self.old_to_new = self.load_if_needed(self.old_to_new, self.file_path())
        for item in _items:
            if item.name in self.old_to_new:
                item.name = self.old_to_new[item.name]
        return [_items]



