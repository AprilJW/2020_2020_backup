import os
import importlib.util
import sys
import logging

_init_file_name = "__init__.py"
_operator_path = os.path.dirname(__file__)


def create_operator(operator_type='', operator_param={}, parent_generator=None):
    """
    """
    operator_list = os.listdir(_operator_path)
    for operator in operator_list:
        init_file_path = os.path.join(_operator_path, operator, _init_file_name)

        if not os.path.isfile(init_file_path):
            continue
        try:
            spec = importlib.util.spec_from_file_location(_init_file_name, init_file_path)
        except:
            logging.error("importlib.util.spec_from_file_location error:" +sys.exc_info()[0])
        if spec is None:
            continue
        operator_init = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(operator_init)
        except:
            logging.info("spec.loader.exec_module" +sys.exc_info()[0])
        try:
            operator_param['parent_generator'] = parent_generator
            operator = operator_init.operator_type_to_operator[operator_type](**operator_param)
            operator.parent_generator = parent_generator
            return operator
        except:
            # key error
            pass
    return None


def get_all_operator():
    operator_lib_list = os.listdir(_operator_path)
    operator_dict = {}
    for operator_lib in operator_lib_list:
        init_file_path = os.path.join(_operator_path, operator_lib, _init_file_name)

        if not os.path.isfile(init_file_path):
            continue
        try:
            spec = importlib.util.spec_from_file_location(_init_file_name, init_file_path)
        except:
            logging.error("importlib.util.spec_from_file_location error:"+ sys.exc_info()[0])
        if spec is None:
            continue
        operator_init = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(operator_init)
        except:
            logging.info("spec.loader.exec_module"+ sys.exc_info()[0])
        try:
            operator_dict.update(operator_init.operator_type_to_operator)
        except:
            # key error
            pass

    return operator_dict
