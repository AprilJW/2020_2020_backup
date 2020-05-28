import json
from functools import singledispatch
from generate_data import Item2D
from generate_data import DataGenerator2D
from ui.property.ProcessorProperty import DirPath
from ui.property.ProcessorProperty import FilePath
from ui.property.ProcessorProperty import EnumOpts
@singledispatch
def convert(o):
    raise TypeError('type not regist to convert')


@convert.register(Item2D.Item2D)
def _(o):
    return None

@convert.register(DataGenerator2D.DataGenerator2D)
def _(o):
    return o.name

@convert.register(DirPath)
def _(o):
    return o()

@convert.register(FilePath)
def _(o):
    return o()

@convert.register(EnumOpts)
def _(o):
    return o.get_enum_list()

class ExtendJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return convert(obj)
        except TypeError:
            return super(ExtendJSONEncoder, self).default(obj)
