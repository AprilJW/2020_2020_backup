import json
import numpy as np

class JsonUtil:
    def __init__(self, data=None):
        if data is not None:
            self.__dict__ = data

    def toJson(self):
        data = json.dumps(self, default=lambda o: o.__dict__ if type(o) is not np.ndarray else o.tolist(),
                          sort_keys=True, indent=4)
        return data

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as f:
            json_reader = JsonUtil(json.load(f))
            return json_reader

    @classmethod
    def to_file(cls, json_obj, file_path):
        with open(file_path, 'w+') as f:
            f.write(json_obj.toJson())
