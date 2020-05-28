from enum import Enum, unique
from generate_data.ItemProcessor import ItemProcessor
from ui.property.ProcessorProperty import EnumOpts
from util import item_algo
import cv2

@unique
class IlluminationTypeEnum(Enum):
    Retinex_SSR = 0
    Retinex_MSR = 1
    BgAdjust = 2

class IlluminationNormalization(ItemProcessor):
    type = 'IlluminationNormalization'
    inputs = {'image'}
    outputs = ['image']

    def __init__(self, illumination_selected_type = None,
                 SSR_kernelSize = 21, mean_illumination = 100,
                 MSR_kernelSize1 = 15, MSR_kernelSize2 = 81, MSR_kernelSize3 = 201,
                 BG_roi_x = 30, BG_roi_y = 700, BG_roi_width = 200, BG_roi_height = 200,
                 **kwargs):

        super().__init__(**kwargs)
        illumination_types = list(IlluminationTypeEnum.__members__.keys())
        if not illumination_selected_type:
            illumination_selected_type = illumination_types[1]

        self.method = EnumOpts(illumination_types, illumination_selected_type)

        self.SSR_kernelSize = SSR_kernelSize
        self.mean_illumination = mean_illumination
        self.MSR_kernelSize1 = MSR_kernelSize1
        self.MSR_kernelSize2 = MSR_kernelSize2
        self.MSR_kernelSize3 = MSR_kernelSize3
        self.BG_roi_x = BG_roi_x
        self.BG_roi_y = BG_roi_y
        self.BG_roi_width = BG_roi_width
        self.BG_roi_height = BG_roi_height

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)

        _image = key_to_inputs['image']
        print(self.type, 'running')
        if _image is None:
            return None
        B, G, R, mask = cv2.split(_image)
        BGR_image = cv2.merge([B, G, R])
        if self.method.selected_opt == IlluminationTypeEnum.Retinex_MSR.name:
            BGR_image = item_algo.retinex_msr(BGR_image, self.MSR_kernelSize1, self.MSR_kernelSize2, self.MSR_kernelSize3, self.mean_illumination)
        elif self.method.selected_opt == IlluminationTypeEnum.Retinex_SSR.name:
            BGR_image = item_algo.retinex_ssr(BGR_image, self.SSR_kernelSize, self.mean_illumination)
        elif self.method.selected_opt == IlluminationTypeEnum.BgAdjust.name:
            BGR_image = item_algo.adjustMeanVal(BGR_image, self.BG_roi_x, self.BG_roi_y, self.BG_roi_width, self.BG_roi_height, self.mean_illumination)
        BGRM_image = cv2.merge([BGR_image, mask])
        return [BGRM_image]




if __name__ == "__main__":

    print(IlluminationTypeEnum.__members__.keys())
