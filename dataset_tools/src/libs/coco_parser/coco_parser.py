import json
import os

class CocoParser():
    def __init__(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.coco_json_data = json.loads(f.readline())
        self.image_name_to_id = {}

    def gather_image_names(self):
        for image in self.coco_json_data['images']:
            self.image_name_to_id[image['file_name']] = image['id']
            
    def get_img_names(self):
        return [i['file_name'] for i in self.coco_json_data['images']]

    def gather_segs_with_label(self, img_name):
        image_id = self.image_name_to_id[img_name]
        segs_with_label = [] #segs means one contour
        category_names = []
        for anno_json in self.coco_json_data['annotations']:
            if anno_json['image_id'] == image_id:
                category_names.append(self.get_category_name(anno_json['category_id']))
                for seg_json in anno_json['segmentation']:
                    segs_with_label.append((self.get_category_name(anno_json['category_id']), seg_json))
        return segs_with_label, category_names

    def get_category_names(self):
        names = []
        for category in self.coco_json_data['categories']:
            names.append(category['name'])
        return set(names)
      
    def get_category_name(self, category_id):
        for category in self.coco_json_data['categories']:
            if category_id == category['id']:
                return category['name']
        return None


if __name__ == '__main__':
    File_name = r'C:\Users\mqd\Desktop\instances_train2014.json'
    image_idx = 0

    coco_parser = CocoParser(File_name)
    imglist = os.listdir(r'C:\Users\mqd\Desktop\train2014\train2014')
    coco_parser.gather_image_names()

    while True:
        input('press any key to continue')
        segs, category_id = coco_parser.gather_segs_category_id(imglist[image_idx])
        print(imglist[image_idx], segs)
        name = coco_parser.gather_category_name(category_id)
        print(name)
        image_idx += 1



