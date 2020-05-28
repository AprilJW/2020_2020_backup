import json

# Class that contains the information of a single annotated object
class ObjectDescInfo:
    def __init__(self, data = None):
        if data is None:
            self.id = 0
            self.label = ""
            self.contours = []
            self.hierarchy = []
            self.bndbox = []
            self.rot_box=[]
            self.is_covered = False
            self.difficult = 0
            self.keypoints = []
        else:
            self.__dict__ = data

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

# The annotation of a whole image
class JsonParserIO:
    def __init__(self, data = None):
        if data is None:
            self.image_shape = []
            self.keypoints = []
            self.skeleton = []
            self.objects = []
        else:
            self.__dict__ = data

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as f:
            """
            jsonText = f.read()
            json_reader = JsonParserIO(json.loads(jsonText))
            """
            json_reader = JsonParserIO(json.load(f))
            objects = []
            for obj in json_reader.objects:
                objects.append(ObjectDescInfo(obj))
            
            json_reader.objects = objects
            return json_reader
        
def write_json(json_parser, file_path):
        with open(file_path, 'w+') as f:
            f.write(json_parser.toJson())

if __name__ == '__main__':
    mask_anno = JsonParserIO.from_file("D://data//visualize_label//json//labels//2007_000000.json")
    #write_json(mask_anno, "D://data//visualize_label//json//test.json")

