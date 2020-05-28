import os
import importlib.util

_init_file_name = "__init__.py"
_formatter_path = os.path.dirname(__file__)


def construct_formatter(dataset_type):
    init_file_path = os.path.join(_formatter_path, _init_file_name)
    if not os.path.isfile(init_file_path):
        return {}
    spec = importlib.util.spec_from_file_location(_init_file_name, init_file_path)
    if spec is None:
        return {}
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    # construct specific formatter
    return plugin.formatter_dict[dataset_type]()

