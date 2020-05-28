from libs.dataset_format.voc_format.VocFormatter import VocFormatter
from libs.dataset_format.coco_format.CocoFormatter import CocoFormatter
from libs.dataset_format.cityscapes_format.CsFormatter import CsFormatter

# Key: dataset type; Value: dataset formatter
formatter_dict = {VocFormatter.FORMATTER_TYPE: VocFormatter,
                  CocoFormatter.FORMATTER_TYPE: CocoFormatter,
                  CsFormatter.FORMATTER_TYPE: CsFormatter}