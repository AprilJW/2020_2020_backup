import cv2
import numpy as np
from PIL import Image

def changePixelsValue(filePath, old_values, new_value, is_modify_none_zero=True):
    mask_img = Image.open(filePath)
    palette = mask_img.getpalette()
    arr = np.array(mask_img)
    if is_modify_none_zero:
        new_arr = np.where(arr > 0, new_value, arr)
    else:
        for old_value in old_values:
            new_arr = np.where(arr == old_value, new_value, arr)
            arr = new_arr
    new_img = Image.fromarray(new_arr)
    if palette is not None:  # for 'L' type image, has no palette
        new_img.putpalette(palette)
    new_img.save(filePath)


def cal_bndbox_max_length(img):
    _, _, _, a = cv2.split(img)  # only use channel 4 for seed image
    _, contours, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(cv2.minAreaRect(contours[0])[1])  # [(x,y), (w,h), (angel)] = cv2.minAreaRect


def get_rotation_box(contour=None):
    """
    get rotation  in [[cx,cy],[w,h],theta]
        w>h,theta represent The angle between the long axis and the x axis
    :param contour:
    :return: [[cx,cy],[w,h],theta]
    """
    if contour is None:
        return
    rot_box = cv2.minAreaRect(contour)
    corner_pt = cv2.boxPoints(rot_box)
    rot_box_edge = [corner_pt[1] - corner_pt[0], corner_pt[3] - corner_pt[0]]
    np.linalg.norm(rot_box_edge)
    wh_idx = sorted((np.linalg.norm(edge), idx) for idx, edge in enumerate(rot_box_edge))
    long_axis = rot_box_edge[wh_idx[1][1]]
    theta = np.arctan2(long_axis[1], long_axis[0])
    if theta > np.pi / 2.0:
        theta -= np.pi
    if theta < -np.pi / 2.0:
        theta += np.pi
    return [[float(rot_box[0][0]), float(rot_box[0][1])], [float(
        wh_idx[1][0]), float(wh_idx[0][0])], float(-theta * 180 / np.pi)]


if __name__ == '__main__':
    pass
