import os
import copy
import json
import numpy as np

from generate_data import DataGenerator2D
from generate_data.GenerateConfig import GenerateConfig
from cutout.ImageGallery import ImageGallery
from generate_data.JSONEncoder import ExtendJSONEncoder
from util.property_utils import gen_properties_template, gen_item_order_and_desc
from ui.property.ProcessorProperty import DirPath, FilePath, EnumOpts
from ui.property.PropertyToWidget import str_to_type

order_tooltip_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "projects/order_tooltip.json"))

property_template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "property_template"))

min_image_size = 500
max_image_size = 1024
max_image_num = 1000
stop_conditon = 'By Image Num'
MAX_DensityMax = 5

image_gallery = ImageGallery()      

def random_load_seed(seed_dir,target_dir):
    seed_list = image_gallery.random_load_multi_items(objects_path=seed_dir)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    with open(os.path.join(target_dir, 'seed.json'), 'w') as fout:
        fout.write(json.dumps(seed_list, indent=4, cls=ExtendJSONEncoder))
    

def gen_random_settings_with_type(settings_template, bg_dir):
    '''
    act as random value, Used in automated testing
    '''
    must_choices = ["SeedItemPicker", "ItemBlender", "ItemsToImage", "GenStopCond"]
    #randomhighlight is unusable, other options' parameter range are not clear ,so set this option false temporarily
    unavailable = ["RandomHighLight","Distortion","Contrast","IlluminationNormalization"]
    image_size_choices = ["file_bg", "color_bg", "random_noise_bg", "Move", "ItemBlender"]
    image_height = np.random.randint(min_image_size, max_image_size)
    image_width = np.random.randint(min_image_size, max_image_size)
    bg_choices = ["file_bg", "color_bg"]
    random_settings_with_type = {}
    for key1 in settings_template:
        new_dict = copy.deepcopy(settings_template[key1])
        for key2 in settings_template[key1].keys():
            value_type_str = new_dict[key2]["type"]
            if value_type_str == "EnumOpts":
                new_dict[key2] = EnumOpts(enum_list=new_dict[key2]["value_options"], enum_opt=np.random.choice(new_dict[key2]["value_options"]))
            elif value_type_str == "int":
                new_dict[key2] = np.random.randint(int(new_dict[key2]["minimum"]), int(new_dict[key2]["maximum"]))
            elif value_type_str == "float":
                new_dict[key2] = np.random.uniform(float(new_dict[key2]["minimum"]), float(new_dict[key2]["maximum"]))
            elif value_type_str == "bool":
                new_dict[key2] = bool(np.random.choice([0, 1]))                                                                                                                
            else:
                new_dict[key2] = str_to_type[value_type_str](new_dict[key2]["value"])
        if key1 in must_choices:
            new_dict["is_used"] = True
        if key1 in unavailable:
            new_dict["is_used"] = False
        if key1 in image_size_choices:
            new_dict["image_height"] = image_height
            new_dict["image_width"] = image_width
        random_settings_with_type[key1] = new_dict
    if random_settings_with_type[bg_choices[0]]["is_used"]:
        random_settings_with_type[bg_choices[0]]["dir_path"] = bg_dir
    else:
        random_settings_with_type[bg_choices[1]]["is_used"] = True
    #set this option false because there is no attachment
    random_settings_with_type[must_choices[0]]["is_add_attachment"] = False
    random_settings_with_type = set_resize_range(settings=random_settings_with_type, template=settings_template, height=image_height, width=image_width)
    random_settings_with_type = check_logic(random_settings_with_type, settings_template)
    return random_settings_with_type
  
  
def check_logic(settings, template):
    for key1 in settings:
        upper_and_max_keys = list(filter(lambda key2 : 'upper' in key2 or 'max' in key2, settings[key1].keys()))
        for upper_key in upper_and_max_keys:
            if 'upper' in upper_key:
                lower_key = upper_key.replace('upper','lower')
            if 'max' in upper_key:
                lower_key = upper_key.replace('max','min')
                if lower_key not in settings[key1].keys():
                    continue
            if settings[key1][upper_key] < settings[key1][lower_key]:
                settings[key1][upper_key],settings[key1][lower_key] = settings[key1][lower_key],settings[key1][upper_key]
            if settings[key1][upper_key] == settings[key1][lower_key]:
                settings[key1][lower_key] = str_to_type[template[key1][lower_key]["type"]](np.random.rand()*settings[key1][upper_key])
    return settings


def set_resize_range(settings={}, template={}, height=1024, width=1024):
    max_shape = image_gallery.get_max_image_shape()
    resize_upper = min(height, width)/max_shape
    settings["Resize"]["resize_ratio_upper"] = np.random.uniform(template["Resize"]["resize_ratio_upper"]["minimum"], resize_upper-1)
    settings["Resize"]["resize_ratio_lower"] = np.random.uniform(template["Resize"]["resize_ratio_lower"]["minimum"], resize_upper-1)
    return settings
    
                    
def create_data_generator(bg_dir):
    items_with_order = gen_item_order_and_desc(order_tooltip_path)[0]
    template = gen_properties_template(property_template_path)    
    random_settings = gen_random_settings_with_type(template, bg_dir)
    generator_json = {
        "name":"config",
        "operator_types": items_with_order,
        "operator_type_to_param": random_settings,
        "project_path": ""}
    new_data_generator = DataGenerator2D.DataGenerator2D()
    new_data_generator.from_json(generator_json)
    return new_data_generator, random_settings    
            

def create_generator_config(random_settings):
    random_generate_image_num = np.random.randint(1, max_image_num)    
    new_generate_config = GenerateConfig(random_settings)
    new_generate_config.generate_image_num = random_generate_image_num
    new_generate_config.stop_condition = stop_conditon
    new_generate_config.label_to_items = image_gallery.label_to_items
    new_generate_config.label_to_density_gennum = new_generate_config.update_label_to_density_gennum(label_to_items=image_gallery.label_to_items)
    for key in new_generate_config.label_to_density_gennum:
        new_generate_config.label_to_density_gennum[key][GenerateConfig.density_gennum_params[2]] = np.random.randint(0,MAX_DensityMax)   
    return new_generate_config   

def save_config(target_dir,data_generators, generator_name_to_inputs):
    gen_param = {} 
    for data_generator in data_generators:
        gen_param[data_generator.name] = {'generator': data_generator.to_json(),
                                          'input': generator_name_to_inputs[data_generator.name].__dict__}
    with open(os.path.join(target_dir, 'config.json'), 'w') as fout:
            fout.write(json.dumps(gen_param, indent=4, cls=ExtendJSONEncoder))
    