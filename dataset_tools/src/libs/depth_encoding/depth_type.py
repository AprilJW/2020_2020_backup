from enum import Enum


class DEPTH_FILE_TYPE(Enum):
    NONE = 0
    EXR = 1
    IMAGE = 2


class DEPTH_ENCODE_TYPE(Enum):
    NONE = 0
    JET_MAPPING = 1
    SURFACE_NORMAL = 2
    HHA = 3
