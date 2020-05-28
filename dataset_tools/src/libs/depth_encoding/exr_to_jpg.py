import numpy as np
import cv2


def cvt_to_8uc1(img_np, cvt_method=[-1,-1]):
    # For 32FC1 image saved as 8UC4
    if len(img_np.shape) > 2:
        img_np = img_np.view(dtype=np.float32)
        
    min_val = cvt_method[0] if cvt_method[0] > -1 else np.min(img_np)
    max_val = cvt_method[1] if cvt_method[1] > -1 else np.max(img_np)
    
    if max_val > min_val:
        img_np = np.clip(img_np, min_val, max_val) - min_val
        img8_np = np.uint8(img_np * (255.0 / (max_val - min_val)))
    else:
        raise Exception('max_val ' + str(max_val) + ' is not larger than min_val '
                        + str(min_val) + ', stop cvt to 8uc1')
    return img8_np


def exr_to_jpg(exrfile):
    rgbf_np = cv2.imread(exrfile, cv2.IMREAD_UNCHANGED)
    rgbf_np = np.clip(rgbf_np * 1000, 0.0, 65535.0)
    rgb8_np = cvt_to_8uc1(rgbf_np)
    return rgb8_np
