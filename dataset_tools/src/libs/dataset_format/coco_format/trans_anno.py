import json
import os

from libs.dataset_format.coco_format.CocoFormatter import CocoFormatter

class CocoImage():
    def __init__(self):
        # the object ID
        self.id     = -1
        self.width  = -1
        self.height = -1
        self.file_name = ''
        self.license = -1
        self.coco_url = ''
        self.date   = ""

    def fromJsonText(self, jsonDict):
        self.id = int(jsonDict['id'])
        self.width = jsonDict['width']
        self.height = jsonDict['height']
        self.file_name = jsonDict['file_name']
        self.license = int(jsonDict['license'])
        self.coco_url = jsonDict['url']
        self.date = str(jsonDict['date_captured'])

    def toJsonText(self):
        objDict = {}
        objDict['id'] = self.id
        objDict['width'] = self.width
        objDict['height'] = self.height
        objDict['file_name'] = self.file_name
        objDict['license'] = self.license
        objDict['coco_url'] = self.coco_url
        objDict['date_captured'] = self.date
        return objDict

class CocoAnno():
    def __init__(self):
        # the object ID
        self.id         = -1
        self.image_id   = -1
        self.cat_id     = -1
        self.iscrowd    = -1
        self.area       = 0
        self.bbox       = []
        self.segmentation = []
        self.num_keys = -1
        self.keys = []

    def fromJsonText(self, jsonDict):
        self.id = int(jsonDict['id'])
        self.image_id = int(jsonDict['image_id'])
        self.cat_id = int(jsonDict['category_id'])
        self.iscrowd = jsonDict['iscrowd']
        self.area = jsonDict['area']
        self.bbox = jsonDict['bbox']
        self.keys = jsonDict['keypoints']
        key_num = 0
        for i in range(int(len(self.keys) / 3)):
            if (self.keys[3 * i] != 0):
                key_num += 1
        self.num_keys = key_num
        self.segmentation = jsonDict['segmentation']

    def toJsonText(self):
        jsonDict = {}
        jsonDict['id'] = self.id
        jsonDict['image_id'] = self.image_id
        jsonDict['category_id'] = self.cat_id
        jsonDict['iscrowd'] = self.iscrowd
        jsonDict['area'] =  self.area
        jsonDict['bbox'] = self.bbox
        jsonDict['keypoints'] = self.keys
        jsonDict['num_keypoints'] = self.num_keys
        jsonDict['segmentation'] = self.segmentation
        return jsonDict

class TransAnno:
    def __init__(self, obj_type):
        self.obj_type = obj_type
        self.anno_type = 'keypoints'
        self.info = {}
        self.images = []
        self.licenses = []
        self.annotations = []
        self.categories =[]

    def fromJsonText(self, jsonText):
        jsonDict = json.loads(jsonText)
        self.info = {
            "date_created": "2018/01/10",
            "contributor": "Mech-Mind",
            "year": 2018,
            "version": "1.0",
            "url": "http://www.mech-mind.net/",
            "description": "This is 1.0 version of the 2017 MS COCO dataset."
        }
        self.licenses = jsonDict['licenses']

        jsonCat = jsonDict['categories'][0]
        category = {
            "supercategory": jsonCat['supercategory'],
            "id": int(jsonCat['id']),
            "name": jsonCat['name'],
            "keypoints": jsonCat['keypoints'],
            'skeleton' : jsonCat['skeleton']
        }
        self.categories.append(category)

        for imageObject in jsonDict['images']:
            coco_img = CocoImage()
            coco_img.fromJsonText(imageObject)
            self.images.append(coco_img)

        for annoObject in jsonDict['annotations']:
            coco_anno = CocoAnno()
            coco_anno.fromJsonText(annoObject)
            self.annotations.append(coco_anno)

    def fromJsonFile(self, jsonFile):
        if not os.path.isfile(jsonFile):
            print('Error: json file not found: {}'.format(jsonFile))
            return False
        with open(jsonFile, 'r') as f:
            jsonText = f.read()
            self.fromJsonText(jsonText)
        f.close()
        return True

    def toJsonFile(self, json_file):
        images = []
        annos = []
        for img in self.images:
            images.append(img.toJsonDict())
        for anno in self.annotations:
            annos.append(anno.toJsonDict())

        json_content = {'info': self.info,
                        'images': images,
                        'licenses': self.licenses,
                        'annotations': annos,
                        'categories': self.categories
                        }

        json_file.write(json.dumps(json_content))
        json_file.close()

    def transform(self, fpath, surfix, coco_config=CocoFormatter()):
        for mode in coco_config.json_modes:
            json_file = os.path.join(fpath, 'annotations', surfix + '_keypoints_' + mode + '.json')
            if self.fromJsonFile(json_file):
                dest_file = os.path.join(fpath, 'annotations',
                                         'person_keypoints_' + mode + '.json')
                self.toJsonFile(open(dest_file, 'w+'))
                print('Transformed json file is saved at: ', dest_file)
