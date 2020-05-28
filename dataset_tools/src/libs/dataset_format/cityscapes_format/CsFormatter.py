from libs.dataset_format.DatasetFormatter import DatasetFormatter
from libs.dataset_format.dataset_utilities.json_util import JsonUtil
from libs.dir_and_filename_info import *
from libs.dataset_format.cityscapes_format.cityscapesScriptsMaster.cityscapesscripts.preparation import json2img
from libs.dataset_format.dataset_utilities import dataset_util
from libs.json_io.json_parser_io import JsonParserIO


class CsFormatter(DatasetFormatter):
    FORMATTER_TYPE = dataset_util.DATASET_TYPES.CS.name

    def __init__(self):
        super(CsFormatter, self).__init__()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        data = JsonUtil.from_file(config_path)
        self.__dict__.update(data.__dict__)

        self.sub_dirs = self.mode_dirs
        self.set_sub_dirs()
        self.image_modes = []
        self.set_image_modes()
        self._images_num = 0

    def set_sub_dirs(self):
        for mode in self.mode_dirs:
            self.sub_dirs[mode] = self.split_dirs
            for split_type in self.split_dirs:
                self.sub_dirs[mode][split_type] = self.city_dirs
        self.sub_dirs['imglists'] = {}

    def set_image_modes(self):
        for split_type in self.split_dirs:
            for city_name in self.city_dirs:
                mode = os.path.join(self.image_folder, split_type, city_name)
                self.image_modes.append(mode)

    def get_dest_label_filepath(self, label_mode, img_id):
        label_filename = self.get_dest_mode_filename(label_mode, img_id, '_polygons.json')
        return os.path.join(self.get_dest_mode_path(label_mode), label_filename)

    def get_cs_mode_filename(self, mode_folder, city_name, img_id, suffix='.png'):
        return city_name + "_" + '%06i' % img_id + "_" + self.get_city_id(city_name) + '_' + mode_folder + suffix

    def get_cs_relative_image_path(self, mode, img_id):
        image_folder, split_type, city_name = mode.split('/')
        filename = self.get_cs_mode_filename(image_folder, city_name, img_id)
        return os.path.join(image_folder, split_type, city_name, filename)

    def get_cs_imglist_filepath(self, split_mode):
        split_folder, split_type, city_name = split_mode.split('/')
        return os.path.join(self.get_dest_mode_path(split_folder), split_type + '.lst')

    def get_cs_relative_gtFine_mask_path(self, mode, img_id):
        return self.get_dest_mode_filename(mode, img_id, '_labelIds.png')

    def get_cs_split_types(self):
        return list(self.split_dirs.keys())

    def get_city_id(self, cityname):
        return self.city_ids[cityname]

    def map_split_to_image_mode(self, split_type):
        for mode in self.image_modes:
            if split_type in mode:
                return mode

        print("Cannot find image mode for split type %s"%split_type)
        return ''

    def get_image_intervals(self, image_list):
        intervals = {}
        image_total_num = len(image_list)
        train_num = dataset_util.get_mode_num(self.split_ids['train'], image_list)
        val_num = dataset_util.get_mode_num(self.split_ids['val'], image_list)
        intervals[self.map_split_to_image_mode('train')] = [0, train_num]
        intervals[self.map_split_to_image_mode('val')] = [train_num, val_num]
        intervals[self.map_split_to_image_mode('test')] = [val_num, image_total_num]
        return intervals

    def get_split_intervals(self, image_list):
        return self.get_image_intervals(image_list)

    def get_label_intervals(self, image_list):
        return self.get_image_intervals(image_list)

    def get_dest_mode_filename(self, mode, img_id, suffix='.png'):
        mode_folder, split_folder, city_name = mode.split('/')
        filename = self.get_cs_mode_filename(mode_folder, city_name, img_id, suffix)
        return filename

    def write_file_list(self, image_list, split_intervals):
        for image_mode in self.image_modes:
            images_sublist = image_list[split_intervals[image_mode][0]:split_intervals[image_mode][1]]
            imglist_file_lines = []
            for srcfile in images_sublist:
                img_id = dataset_util.get_image_id(srcfile)
                origin_img_path = self.get_cs_relative_image_path(image_mode, img_id)
                label_mode = image_mode.replace(self.image_folder, self.label_folder)
                gtFine_img_path = self.get_cs_relative_gtFine_mask_path(label_mode, img_id)
                imglist_single_line = str(self._images_num) + '\t' + origin_img_path + '\t' + gtFine_img_path + '\n'
                imglist_file_lines.append(imglist_single_line)
                self._images_num += 1
            split_mode = image_mode.replace(self.image_folder, self.split_folder)
            with open(self.get_cs_imglist_filepath(split_mode), 'w') as f_lst:
                f_lst.writelines(imglist_file_lines)

    def generate_cityscape_json(self, src_mask_file, dest_mask_path, label_list):
        mask_anno = JsonParserIO.from_file(src_mask_file)
        image_shape = mask_anno.image_shape
        anno_objects = mask_anno.objects
        cs_area = dataset_util.get_area(image_shape, *self.get_image_size())
        img_seg, cnts_hier = dataset_util.get_masks_from_file(cs_area, anno_objects,
                                                              self.separation_linewidth, label_list)
        object_list = []
        label = 'person'
        for obj_id, img_object in enumerate(anno_objects):
            if dataset_util.is_valid_mask_anno(img_object):
                polygon = []
                final_cnts = cnts_hier[obj_id][0]
                final_hier = cnts_hier[obj_id][1]
                contours_polygon = []
                for contour in final_cnts:
                    points = []
                    for i in range(len(contour)):
                        points.append(contour[i, 0, :].tolist())
                    contours_polygon.append(points)
                if self.generate_hierarchy_json:
                    polygon_dict = {}
                    # print('cityscape hierarchy', final_hier)
                    polygon_dict['hierarchy'] = final_hier.tolist()
                    # polygon_dict['hierarchy'] = final_hier
                    polygon_dict['contours'] = contours_polygon
                    polygon.append(polygon_dict)
                else:
                    polygon = contours_polygon[0]

                single_object = {
                    "label": label,
                    "polygon": polygon
                }
                object_list.append(single_object)

        width = cs_area[2] - cs_area[0]
        height = cs_area[3] - cs_area[1]
        img_json = {"imgHeight": height,
                    "imgWidth": width,
                    "objects": object_list
                    }

        f = open(dest_mask_path, 'w')
        f.write(json.dumps(img_json))
        f.close()

    def gen_cityscapes_masks(self, src_path, dest_path_no_ext):
        outImg_label = dest_path_no_ext + "_labelIds.png"
        outImg_instance = dest_path_no_ext + "_instanceIds.png"
        outImg_color = dest_path_no_ext + "_color.png"

        json2img.main(['-i', src_path, outImg_instance])
        json2img.main(['-l', src_path, outImg_label])
        json2img.main(['-c', src_path, outImg_color])

    def generate_labels_per_mode(self, label_mode, img_id, label_list):
        mask_path = self.get_dest_label_filepath(label_mode, img_id)
        self.generate_cityscape_json(self.get_src_label_filepath(img_id), mask_path, label_list)
        self.gen_cityscapes_masks(mask_path, mask_path.split('_polygons')[0])

    def generate_labels(self, image_list, label_intervals):
        print('generate labels ...')
        label_list = []
        for image_mode in self.image_modes:
            for i in range(label_intervals[image_mode][0], label_intervals[image_mode][1]):
                img_id = dataset_util.get_image_id(image_list[i])
                label_mode = image_mode.replace(self.image_folder, self.label_folder)
                self.generate_labels_per_mode(label_mode, img_id, label_list)

        dataset_util.write_label_id_color_file(label_list, self.get_root_path())
        print('cityscape format done')
