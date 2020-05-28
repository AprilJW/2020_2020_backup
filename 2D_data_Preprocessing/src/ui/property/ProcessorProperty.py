"""
    customer type class file
"""


class DirPath:
    """
        dir path class, make
    """
    def __init__(self, path=''):
        self.dir_path = path

    def __call__(self):
        return self.dir_path


class FilePath:
    def __init__(self, path=''):
        self.file_path = path

    def __call__(self):
        return self.file_path


class EnumOpts:
    def __init__(self, enum_list=[], enum_opt=''):
        self.selected_opt = enum_opt
        self.enum_list = enum_list

    def __call__(self):
        return self.selected_opt

    def get_enum_list(self):
        return self.enum_list

    def get_enum_opt(self):
        return self.selected_opt
    
    def set_selected_opt(self, enum_opt):
        self.selected_opt = enum_opt
