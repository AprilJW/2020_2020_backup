import os
import copy
import ast
import json
from ui.property.ProcessorProperty import DirPath, FilePath, EnumOpts
from ui.property.PropertyToWidget import str_to_type


def gen_properties_template(properties_template_dir):
    '''
    read original settings template json file and return the dict
    params_of jsonfile: 
    "default": for default value,
    "value_list": mainly for comboBox,
    "value_type": for bind_dict func, to generate corresponding widget,
    "min_max": for spinBox and doubleSpinBox,
    "desc": for tool tip,
    "single_step": for spinBox and doubleSpinBox 
    '''
    properties_template = {}
    template_dir = os.path.abspath(properties_template_dir)
    for property_template in os.listdir(template_dir):
        with open(os.path.join(template_dir,property_template)) as f:
            properties_template[os.path.splitext(property_template)[0]] = json.load(f)
    return properties_template


def gen_default_settings_with_type(settings_template):
    '''
    act as default values.
    different from settings_template, which contains default values and widget property settings,
    settings_with_type contains with actual values with specific type
    '''
    default_settings_with_type = {}
    for key1 in settings_template:
        new_dict = copy.deepcopy(settings_template[key1])
        for key2 in settings_template[key1].keys():
            value_type_str = new_dict[key2]["type"]
            if value_type_str == "EnumOpts":
                new_dict[key2] = EnumOpts(enum_list=new_dict[key2]["value_options"], enum_opt=new_dict[key2]["value"])
            else:
                new_dict[key2] = str_to_type[value_type_str](new_dict[key2]["value"])
        default_settings_with_type[key1] = new_dict
    return default_settings_with_type


def gen_concrete_settings_with_type(plain_dict, settings_template):
    concrete_settings_with_type = gen_default_settings_with_type(settings_template)
    for key1 in plain_dict.keys():
        for key2 in plain_dict[key1].keys():
            value_type = settings_template[key1][key2]["type"]
            if value_type == "EnumOpts":
                concrete_settings_with_type[key1][key2].set_selected_opt(plain_dict[key1][key2])
            else:
                concrete_settings_with_type[key1][key2] = str_to_type[value_type](plain_dict[key1][key2])
    return concrete_settings_with_type

def gen_item_order_and_desc(order_desc_path):
    if not os.path.isfile(order_desc_path):
        return {}, {}
    with open(order_desc_path) as f:
        json_file = json.load(f)
    return json_file["order"], json_file["tool_tip"]

def gen_plain_dict(settings_with_type, settings_template):
    '''
    get rid of self-defined data_type
    
    '''
    special_types = (DirPath, FilePath, EnumOpts)
    dic = copy.deepcopy(settings_with_type)
    for key1 in settings_with_type.keys():
        for key2 in settings_with_type[key1].keys():
            if isinstance(dic[key1][key2], special_types):
                dic[key1][key2] = dic[key1][key2]()
            if settings_template[key1][key2]["type"] == "list":
                dic[key1][key2] = ast.literal_eval(dic[key1][key2])
    return dic
