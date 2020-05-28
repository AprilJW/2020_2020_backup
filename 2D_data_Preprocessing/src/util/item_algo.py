from enum import Enum
import copy
import math
import logging

import numpy as np
import cv2
from PIL import Image
from util.img_process_util import *
import logging

def change_brightness(image, brightness, scale=1):
    b, g, r, a = cv2.split(image)
    for channel in [b, g, r]:
        cv2.convertScaleAbs(channel, channel, scale, brightness)
    return cv2.merge([b, g, r, a])


def adjust_gamma(image, gamma=1.0):
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")
    b, g, r, a = cv2.split(image)
    bgr_image = cv2.merge([b, g, r])
    adjusted_image = cv2.LUT(bgr_image, table)
    b, g, r = cv2.split(adjusted_image)
    return cv2.merge([b, g, r, a])


def change_contrast(image, clipLimit=4.0, tileGridSize=(8, 8)):
    b, g, r, alpha = cv2.split(image)
    img = cv2.merge([b, g, r])

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    cl = clahe.apply(l)

    # -----Merge the CLAHE enhanced L-channel with the a and b channel-----------
    limg = cv2.merge((cl, a, b))

    # -----Converting image from LAB Color model to RGB model--------------------
    img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    b, g, r = cv2.split(img)
    return cv2.merge([b, g, r, alpha])


def change_hue(image, target_hue):
    b, g, r, a = cv2.split(image)
    img = cv2.merge([b, g, r])
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img_hsv)

    avg_hsv = np.average(img_hsv, (0, 1))

    param_a = (target_hue - avg_hsv[0]) * 1.0 / ((avg_hsv[0] - 180) * avg_hsv[0])
    param_b = 1 - 180 * param_a
    h = param_a * (h ** 2) + param_b * h
    h = h.astype(np.uint8)
    img_hsv = cv2.merge([h, s, v])
    img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
    b, g, r = cv2.split(img_hsv)
    return cv2.merge([b, g, r, a])


def move(item, image_shape, x, y):
    """
        locate item in image coordinate system
    :param item:
    :param image_shape:
    :param x: center point x
    :param y: center point y
    :return:
    """
    item.bndbox[0] = max(0, int(x - math.floor(item.image.shape[1] / 2)))
    item.bndbox[2] = min(int(image_shape[1] - 1), int(x + math.ceil(item.image.shape[1] / 2)))
    item.bndbox[1] = max(0, int(y - math.floor(item.image.shape[0] / 2)))
    item.bndbox[3] = min(int(image_shape[0] - 1), int(y + math.ceil(item.image.shape[0] / 2)))
    item.rot_box[0][0] += max(0, int(x - math.floor(item.image.shape[1] / 2)))
    item.rot_box[0][1] += max(0, int(y - math.floor(item.image.shape[0] / 2)))

    item.width = item.bndbox[2] - item.bndbox[0]
    item.height = item.bndbox[3] - item.bndbox[1]
    delta_x = max(0, int(math.floor(item.image.shape[1] / 2) - x))
    delta_y = max(0, int(math.floor(item.image.shape[0] / 2) - y))
    for sub_item in item.sub_items:
        sub_item.bndbox[0] = max(0, sub_item.bndbox[0] + int(x - math.floor(item.image.shape[1] / 2)))
        sub_item.bndbox[1] = max(0, sub_item.bndbox[1] + int(y - math.floor(item.image.shape[0] / 2)))
        sub_item.bndbox[2] = min(int(image_shape[1] - 1),
                                 sub_item.bndbox[2] + int(x - math.floor(item.image.shape[1] / 2)))
        sub_item.bndbox[3] = min(int(image_shape[0] - 1),
                                 sub_item.bndbox[3] + int(y - math.floor(item.image.shape[0] / 2)))

        sub_item.rot_box[0][0] += max(0, int(x - math.floor(item.image.shape[1] / 2)))
        sub_item.rot_box[0][1] += max(0, int(y - math.floor(item.image.shape[0] / 2)))
        sub_item.image = sub_item.image[delta_y:item.height + delta_y, delta_x:item.width + delta_x, :]
        sub_item.overlap_mask_img = sub_item.overlap_mask_img[delta_y:item.height + delta_y,
                                    delta_x:item.width + delta_x]
    item.image = item.image[delta_y:item.height + delta_y, delta_x:item.width + delta_x, :]
    item.overlap_mask_img = item.overlap_mask_img[delta_y:item.height + delta_y, delta_x:item.width + delta_x]

    return item


def rotation(item, angle, bndbox=None):
    """
        rotate item and return a new item
    """
    [rows, cols, _] = item.image.shape
    rot_mat = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    cos = np.abs(rot_mat[0, 0])
    sin = np.abs(rot_mat[0, 1])
    new_w = int(rows * sin + cols * cos)
    new_h = int(rows * cos + cols * sin)
    rot_mat[0, 2] += (new_w / 2) - cols / 2
    rot_mat[1, 2] += (new_h / 2) - rows / 2

    rot_img = cv2.warpAffine(item.image, rot_mat, (new_w, new_h))

    b, g, r, a = cv2.split(rot_img)
    # a = img_process.smooth_edges(a, ksize = 5, iterations = 15)
    # rot_img = cv2.merge([b, g, r, a])
    if bndbox is None:
        max_contour = get_max_blob(a)
        bnd_rect = cv2.boundingRect(max_contour)
    else:
        bnd_rect = bndbox
    bndbox = [bnd_rect[0], bnd_rect[1], bnd_rect[0] + bnd_rect[2], bnd_rect[1] + bnd_rect[3]]

    item = replace_img(item, item_img=rot_img[bndbox[1]:bndbox[3], bndbox[0]:bndbox[2]])
    for sub_item in item.sub_items:
        sub_item = rotation(sub_item, angle, bnd_rect)
        sub_item.bndbox = calc_bndbox(sub_item.image)

    return align_to(item)


class CropTypes(Enum):
    top = 0
    bottom = 1
    left = 2
    right = 3
    middle = 4
    random = 5


def crop(item, crop_opt='top', min_w=50, min_h=50, bndbox=None):
    """
        crop item inside target_roi
        supported crop type: top, bottom, left, right middle
    """
    # currently, don't support multi-seed
    if len(item.sub_items) != 0:
        return item

    row, col, _ = item.image.shape

    if min_h >= row or min_w >= col:
        message = '"Crop" algorithm skipped, because min_h ({0}) >= row ({1}) ' \
                  'or min_w ({2}) >= col ({3})'
        logging.error(message.format(min_h, row, min_w, col))
        return item

    crop_types = list(CropTypes.__members__.keys())
    if crop_opt == CropTypes.random.name:
        crop_opt = np.random.choice(crop_types[:-2])

    final_h = np.random.randint(min_h, row + 1)
    final_w = np.random.randint(min_w, col + 1)

    crop_img = np.zeros(item.image.shape).astype(np.uint8)
    if crop_opt == CropTypes.top.name:
        crop_img[:final_h, :, :] = item.image[:final_h, :, :]

    elif crop_opt == CropTypes.bottom.name:
        crop_img[-final_h:, :, :] = item.image[-final_h:, :, :]

    elif crop_opt == CropTypes.left.name:
        crop_img[:, :final_w, :] = item.image[:, :final_w, :]

    elif crop_opt == CropTypes.right.name:
        crop_img[:, -final_w:, :] = item.image[:, -final_w:, :]

    elif crop_opt == CropTypes.middle.name:
        x = np.random.randint(0, row - final_h)
        y = np.random.randint(0, col - final_w)
        crop_img[x:x+final_h, y:y+final_w, :] = item.image[x:x+final_h, y:y+final_w, :]

    b, g, r, a = cv2.split(crop_img)
    if bndbox is None:
        max_contour = get_max_blob(a)
        bnd_rect = cv2.boundingRect(max_contour)
    else:
        bnd_rect = bndbox
    bndbox = [bnd_rect[0], bnd_rect[1], bnd_rect[0] + bnd_rect[2], bnd_rect[1] + bnd_rect[3]]

    item = replace_img(item, item_img=crop_img[bndbox[1]:bndbox[3], bndbox[0]:bndbox[2]])
    return align_to(item)


def replace_img(item, item_img=None, bndbox=None):
    if item_img is None:
        return
    else:
        item.image = item_img

    if bndbox is None:
        item.bndbox = [0, 0, item.image.shape[1], item.image.shape[0]]
    else:
        item.bndbox = bndbox

    b, g, r, a = cv2.split(item.image)
    item.maskContour = get_max_blob(a, 128)
    item.overlap_mask_img = get_max_blob_bin_image(max_contour=item.maskContour, a_img=a,
                                                   is_fill=True)
    item.image = cv2.bitwise_and(item.image, item.image, mask=item.overlap_mask_img)
    item.objArea = cv2.countNonZero(item.overlap_mask_img)
    item.rot_box = get_rotation_box(item.maskContour)

    return item


def resize(item, ratio_height, ratio_width, sigma=1.6, is_gauss_scale=False):
    new_img_width = int(np.floor(item.image.shape[1] * ratio_width))
    new_img_height = int(np.floor(item.image.shape[0] * ratio_height))

    resize_img = cv2.resize(item.image, (new_img_width, new_img_height), interpolation=cv2.INTER_LINEAR)

    if is_gauss_scale:
        sigma, kernel_size = _get_gauss_sigma_and_size(sigma, resize_ratio=ratio_height)
        b, g, r, a = cv2.split(resize_img)
        b = cv2.GaussianBlur(b, (kernel_size, kernel_size), sigma)
        g = cv2.GaussianBlur(g, (kernel_size, kernel_size), sigma)
        r = cv2.GaussianBlur(r, (kernel_size, kernel_size), sigma)
        resize_img = cv2.merge([b, g, r, a])

    item = replace_img(item, item_img=resize_img)
    for sub_item in item.sub_items:
        resize_img = cv2.resize(sub_item.image, (new_img_width, new_img_height), interpolation=cv2.INTER_LINEAR)
        # resize_img = cv2.erode(resize_img,kernel=np.ones((3,3),np.uint8))
        sub_item = replace_img(sub_item, item_img=resize_img, bndbox=calc_bndbox(resize_img))

    return align_to(item)


def random_highlight(image, min_hl_num, max_hl_num, min_hl_area=10, max_hl_area=100):
    seed_a = image[:, :, -1]
    seed_rgb = image[:, :, :3]
    seed_height, seed_width = image.shape[:2]
    hl_num = np.random.randint(min_hl_num, max_hl_num)
    hl_b = np.zeros((seed_height, seed_width)).astype('uint8')
    hl_g = np.zeros((seed_height, seed_width)).astype('uint8')
    hl_r = np.zeros((seed_height, seed_width)).astype('uint8')
    for hl_index in range(hl_num):
        hl_mask = get_high_light_mask(seed_height, seed_width)
        while not check_area(hl_mask, min_area=min_hl_area, max_area=max_hl_area):
            hl_mask = get_high_light_mask(seed_height, seed_width)
        hl_mask = fill_holes(hl_mask)
        hl_b = np.where((hl_mask > 0) | (hl_b > 0), np.random.randint(245, 255), 0)
        hl_g = np.where((hl_mask > 0) | (hl_g > 0), np.random.randint(245, 255), 0)
        hl_r = np.where((hl_mask > 0) | (hl_r > 0), np.random.randint(245, 255), 0)
    hl_rgb = cv2.merge((hl_b, hl_g, hl_r))
    seed_hl_mask = np.where(hl_rgb > 0, seed_rgb, 0)
    delta_mask = np.subtract(hl_rgb, seed_hl_mask)
    np.clip(delta_mask, 0, 255, out=delta_mask)
    delta_mask = cv2.blur(delta_mask, (5, 5))
    noise_mask = np.random.normal(scale=2, size=delta_mask.shape).astype(np.int32)
    delta_mask = np.where(delta_mask > 0, delta_mask + noise_mask, 0)
    new_img_added = np.add(seed_rgb, delta_mask)
    new_img_cliped = np.clip(new_img_added, 0, 255, out=new_img_added)
    return np.dstack((new_img_cliped, seed_a)).astype(np.uint8)


def add_shadow(item, shade_offset, shade_scale=1):
    shadow_image = change_brightness(item.image, shade_offset, shade_scale)
    b_line_x = np.random.randint(0, int(shadow_image.shape[1]))
    b_line_y = np.random.randint(0, int(shadow_image.shape[0]))
    e_line_x = np.random.randint(0, int(shadow_image.shape[1]))
    e_line_y = np.random.randint(0, int(shadow_image.shape[0]))
    y_top = 0
    y_bottom = item.image.shape[0]
    if b_line_x != e_line_x:
        x_top = int((0 - e_line_y) * (b_line_y - e_line_y) / (b_line_x - e_line_x) + e_line_x)
        x_bottom = int((item.image.shape[0] - e_line_y) * (b_line_y - e_line_y) / (b_line_x - e_line_x) + e_line_x)
    else:
        x_top = b_line_x
        x_bottom = e_line_x
    shadow_mask = np.zeros((item.image.shape[0], item.image.shape[1]), np.uint8)
    shadow_mask.fill(255)
    cv2.line(shadow_mask, (x_top, y_top), (x_bottom, y_bottom), 0, 3, cv2.LINE_8)
    _, cnts, hier = cv2.findContours(shadow_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    idx = np.random.choice(len(cnts))
    cnt = cnts[idx]
    cv2.drawContours(shadow_mask, [cnt], 0, 0, cv2.FILLED, cv2.LINE_8)
    shadow_mask = erode_gauss_blur(shadow_mask, ksize=7)
    shadow_mask = cv2.bitwise_and(shadow_mask, item.overlap_mask_img)
    b, g, r, a = cv2.split(shadow_image)
    shadow_mask = cv2.bitwise_and(shadow_mask, a)
    shadow_image = cv2.merge([b, g, r, shadow_mask])
    item.image = paint_on(shadow_image, item.image)
    return item


def align_to(item):
    """
        set bndbox to [0,0,width,height]
        each part bound box related to bndbox left top corner
    """
    item.bndbox[0] = 0
    item.bndbox[1] = 0
    item.bndbox[2] = item.image.shape[1]
    item.bndbox[3] = item.image.shape[0]
    return item


def _get_gauss_sigma_and_size(sigma, resize_ratio):
    sigma_new = sigma + 1 / resize_ratio
    kernel_size = sigma * 3 if int(sigma * 3) % 2 == 1 else sigma * 3 + 1
    return sigma_new, int(kernel_size)


def _add_attachment(item, attachment_item_input):
    attachment_item = copy.deepcopy(attachment_item_input)

    item_shape = item.image.shape
    attachment_shape = attachment_item.image.shape

    if any(np.asarray(attachment_shape[:-1]) >= np.asarray(item_shape[:-1])):
        message = '"Add attachment" algorithm skipped, because attachment shape {0} >= ' \
                  'item shape {1}'
        logging.error(message.format(attachment_shape[:-1], item_shape[:-1]))
        return None

    attachment_item = rotation(item=attachment_item, angle=np.random.randint(0, 360, size=1))
    x1 = int(attachment_shape[1] / 2)
    y1 = int(attachment_shape[0] / 2)

    margin_width = min(x1, y1)
    # margin_width = 0
    x_move = np.random.randint(margin_width, item_shape[1] - margin_width, size=1)
    y_move = np.random.randint(margin_width, item_shape[0] - margin_width, size=1)

    _, _, _, a_move_before = cv2.split(attachment_item.image)
    attachment_item = move(attachment_item, item_shape, x_move, y_move)
    _, _, _, a_move_after = cv2.split(attachment_item.image)
    a_move_before_points = cv2.findNonZero(a_move_before)
    a_move_after_points = cv2.findNonZero(a_move_after)
    if a_move_before_points is None or a_move_after_points is None:
        return None
    if len(a_move_after_points) < len(a_move_before_points) - 10:
        return None
    x1 = attachment_item.bndbox[0]
    y1 = attachment_item.bndbox[1]
    x2 = attachment_item.bndbox[2]
    y2 = attachment_item.bndbox[3]

    b, g, r, a = cv2.split(attachment_item.image)
    image_with_attachment = item.image.copy()
    _, _, _, a_img = cv2.split(image_with_attachment)
    a_img_rev = cv2.bitwise_not(a_img)
    a_attachment_large_canvas = np.zeros(a_img_rev.shape, np.uint8)
    a_attachment_large_canvas[y1:y2, x1:x2] = a.copy()

    a_overflow = cv2.bitwise_and(a_attachment_large_canvas, a_img_rev)
    overflow_points = cv2.findNonZero(a_overflow)
    if overflow_points is not None and len(overflow_points) > 10:
        return None

    a_attachment_large_canvas = cv2.erode(a_attachment_large_canvas, np.ones((5, 5), np.uint8), 1)
    # _, a_attachment_large_canvas = cv2.threshold(a_attachment_large_canvas, 250, 255, cv2.THRESH_BINARY)
    a_attachment_large_canvas = cv2.bitwise_and(a_attachment_large_canvas, a_img)
    attachment_image = cv2.merge([b, g, r, a_attachment_large_canvas[y1:y2, x1:x2]])
    image_with_attachment[y1:y2, x1:x2] = paint_on(attachment_image,
                                                   image_with_attachment[y1:y2, x1:x2])
    # img_process_util.image_show('attached', image_with_attachment, 255)
    return image_with_attachment


def add_attachment(item, attachment_items, attachemnt_list):
    attachemnt_list_stoachastic = attachemnt_list.copy()

    for attach_type, items in attachment_items.items():
        if int(attachemnt_list[attach_type]['prob']) == 1 and attachemnt_list[attach_type]['num'] > 0:
            attachemnt_list_stoachastic.pop(attach_type)
            for i in range(attachemnt_list[attach_type]['num']):
                attachment_item_img = _add_attachment(item, items[0])
                if attachment_item_img is not None:
                    item = replace_img(item, attachment_item_img)
        elif attachemnt_list[attach_type]['prob'] == 0:
            attachemnt_list_stoachastic.pop(attach_type)

    if len(attachemnt_list_stoachastic) > 0:
        attach_types = list(attachemnt_list_stoachastic.keys())
        attach_probs = []
        for attach_type in attach_types:
            attach_probs.append(attachemnt_list_stoachastic[attach_type]['prob'])

        attach_type = np.random.choice(attach_types, 1, p=attach_probs)[0]
        for i in range(attachemnt_list_stoachastic[attach_type]['num']):
            attachment_item = _add_attachment(attachment_items[attach_type][0])
            if attachment_item is not None:
                item = replace_img(item, attachment_item)

    return item


def random_distortion(image, grid_width=4, grid_height=4, magnitude=4):
    """
    Distorts the passed image(s) according to the parameters supplied during
    instantiation, returning the newly distorted image.
    
    :param images: The image(s) to be distorted.
    :type images: List containing PIL.Image object(s).
    :return: The transformed image(s) as a list of object(s) of type
     PIL.Image.
    """
    pil_img = Image.fromarray(image)

    w, h = pil_img.size

    horizontal_tiles = grid_width
    vertical_tiles = grid_height

    width_of_square = int(math.floor(w / float(horizontal_tiles)))
    height_of_square = int(math.floor(h / float(vertical_tiles)))

    width_of_last_square = w - (width_of_square * (horizontal_tiles - 1))
    height_of_last_square = h - (height_of_square * (vertical_tiles - 1))

    dimensions = []

    for vertical_tile in range(vertical_tiles):
        for horizontal_tile in range(horizontal_tiles):
            if vertical_tile == (vertical_tiles - 1) and horizontal_tile == (horizontal_tiles - 1):
                dimensions.append([horizontal_tile * width_of_square,
                                   vertical_tile * height_of_square,
                                   width_of_last_square + (horizontal_tile * width_of_square),
                                   height_of_last_square + (height_of_square * vertical_tile)])
            elif vertical_tile == (vertical_tiles - 1):
                dimensions.append([horizontal_tile * width_of_square,
                                   vertical_tile * height_of_square,
                                   width_of_square + (horizontal_tile * width_of_square),
                                   height_of_last_square + (height_of_square * vertical_tile)])
            elif horizontal_tile == (horizontal_tiles - 1):
                dimensions.append([horizontal_tile * width_of_square,
                                   vertical_tile * height_of_square,
                                   width_of_last_square + (horizontal_tile * width_of_square),
                                   height_of_square + (height_of_square * vertical_tile)])
            else:
                dimensions.append([horizontal_tile * width_of_square,
                                   vertical_tile * height_of_square,
                                   width_of_square + (horizontal_tile * width_of_square),
                                   height_of_square + (height_of_square * vertical_tile)])

    # For loop that generates polygons could be rewritten, but maybe harder to read?
    # polygons = [x1,y1, x1,y2, x2,y2, x2,y1 for x1,y1, x2,y2 in dimensions]

    # last_column = [(horizontal_tiles - 1) + horizontal_tiles * i for i in range(vertical_tiles)]
    last_column = []
    for i in range(vertical_tiles):
        last_column.append((horizontal_tiles - 1) + horizontal_tiles * i)

    last_row = range((horizontal_tiles * vertical_tiles) - horizontal_tiles, horizontal_tiles * vertical_tiles)

    polygons = []
    for x1, y1, x2, y2 in dimensions:
        polygons.append([x1, y1, x1, y2, x2, y2, x2, y1])

    polygon_indices = []
    for i in range((vertical_tiles * horizontal_tiles) - 1):
        if i not in last_row and i not in last_column:
            polygon_indices.append([i, i + 1, i + horizontal_tiles, i + 1 + horizontal_tiles])

    def do(pil_img):

        for a, b, c, d in polygon_indices:
            dx = np.random.randint(-magnitude, magnitude)
            dy = np.random.randint(-magnitude, magnitude)

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[a]
            polygons[a] = [x1, y1,
                           x2, y2,
                           x3 + dx, y3 + dy,
                           x4, y4]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[b]
            polygons[b] = [x1, y1,
                           x2 + dx, y2 + dy,
                           x3, y3,
                           x4, y4]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[c]
            polygons[c] = [x1, y1,
                           x2, y2,
                           x3, y3,
                           x4 + dx, y4 + dy]

            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[d]
            polygons[d] = [x1 + dx, y1 + dy,
                           x2, y2,
                           x3, y3,
                           x4, y4]

        generated_mesh = []
        for i in range(len(dimensions)):
            generated_mesh.append([dimensions[i], polygons[i]])

        return pil_img.transform(pil_img.size, Image.MESH, generated_mesh, resample=Image.BICUBIC)

    distorted_pil_img = do(pil_img)
    return np.array(distorted_pil_img)


def get_item_mask_in_origin_img(item_image=None, bndbox=None, image_width=1292, image_height=964):
    if item_image is None:
        return None
    if bndbox is None:
        return None
    if len(item_image.shape) == 3:
        b, g, r, alpha = cv2.split(item_image)
    elif len(item_image.shape) == 2:
        alpha = item_image
    else:
        raise TypeError('item_image is not 4-ch | 1-ch')
    _, alpha = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)  # make sure mask is binary image
    item_mask = np.zeros((image_height, image_width), np.uint8)
    item_mask[bndbox[1]:bndbox[3], bndbox[0]:bndbox[2]] = alpha
    return item_mask
    pass


def efface_covered_item(item_upper_mask, item_lower, parent_bndbox=None, image_width=1292, image_height=964):
    if parent_bndbox is None:
        parent_bndbox = item_lower.bndbox
    item_lower_mask = get_item_mask_in_origin_img(item_image=item_lower.overlap_mask_img, bndbox=parent_bndbox,
                                                  image_width=image_width, image_height=image_height)
    mask_interact_rev = cv2.bitwise_not(cv2.bitwise_and(item_lower_mask, item_upper_mask))
    overlap_mask_img = cv2.bitwise_and(item_lower.overlap_mask_img, mask_interact_rev[parent_bndbox[1]:parent_bndbox[3],
                                                                    parent_bndbox[0]:parent_bndbox[2]])
    return overlap_mask_img

#Illumination method1
def retinex_msr(color_img, nkernelSize1, nkernelSize2, nkernelSize3, mean_illumination, DARK_THRESHOLD=10, ADJUST_DELTA=10):
    if color_img is None:
        return None
    #DARK_THRESHOLD is better between 5 and 50
    if DARK_THRESHOLD == 0:
        logging.warning('(retinex_msr)DRAK_THRESHOLD can not be 0, adjust to 0.005 automatically!!!')
        DARK_THRESHOLD = 0.005
    hsv_split = adjust_dark_pixel(color_img, DARK_THRESHOLD, ADJUST_DELTA)
    r_part_32F1 = split_r_part(hsv_split[2],  nkernelSize1, mean_illumination)
    r_part_32F2 = split_r_part(hsv_split[2], nkernelSize2, mean_illumination)
    r_part_32F3 = split_r_part(hsv_split[2], nkernelSize3, mean_illumination)
    r_part_32F = (r_part_32F1 + r_part_32F2 + r_part_32F3) / 3
    hsv_split[2] = r_part_32F.astype(np.float32)
    hsv_image = cv2.merge(hsv_split)
    color_img_32F = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    adjust_img = color_img_32F.astype(color_img.dtype)
    return adjust_img

#Illumination method2
def retinex_ssr(color_img, nkernelSize, mean_illumination, DARK_THRESHOLD=10, ADJUST_DELTA=10):
    if color_img is None:
        return None
    # DARK_THRESHOLD is better between 5 and 50
    if DARK_THRESHOLD == 0:
        logging.warning('(retinex_ssr)DRAK_THRESHOLD can not be 0, adjust to 0.005 automatically!!!')
        DARK_THRESHOLD = 0.005
    hsv_split = adjust_dark_pixel(color_img, DARK_THRESHOLD, ADJUST_DELTA)
    r_part_32F = split_r_part(hsv_split[2], nkernelSize, mean_illumination)
    hsv_split[2] = r_part_32F.astype(np.float32)
    hsv_img = cv2.merge(hsv_split)
    color_img_32F = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
    adjust_img = color_img_32F.astype(color_img.dtype)
    return adjust_img

#Illumination method3
def adjustMeanVal(color_img, roi_x, roi_y, roi_width, roi_height, after_mean):
    if color_img is None:
        return None
    before_mean = calMeanVal(color_img, roi_x, roi_y, roi_width, roi_height)
    if before_mean == 0:
        return color_img
    color_img_32F = color_img.astype(np.float32)
    hsv_img = cv2.cvtColor(color_img_32F, cv2.COLOR_BGR2HSV)
    hsv_split = cv2.split(hsv_img)
    hsv_split[2] = hsv_split[2] * after_mean / before_mean
    hsv_split[2][hsv_split[2] > 255] = 255
    hsv_img = cv2.merge(hsv_split)
    color_img_32F = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
    adjust_img = color_img_32F.astype(color_img.dtype)
    return adjust_img


def adjust_dark_pixel(color_img, DARK_THRESHOLD, ADJUST_DELTA):
    color_img_32F = color_img.astype(np.float32)
    hsv_img = cv2.cvtColor(color_img_32F, cv2.COLOR_BGR2HSV)
    # the locations of v_channel value less than DARK_THRESHOLD
    locs = np.where(hsv_img[:, :, 2] < DARK_THRESHOLD)
    if len(locs[0]) > 0 and len(locs[1]) > 0 :
        hsv_img[locs[0], locs[1], 1] = (hsv_img[locs[0], locs[1], 2] / DARK_THRESHOLD) * hsv_img[locs[0], locs[1], 1]
        hsv_img[locs[0], locs[1], 2] += ADJUST_DELTA
    return cv2.split(hsv_img)

#Get the original object component
def split_r_part(hsv_v, nkernelSize, mean_illumination, ADJUST_DELTA = 10):
    v_blur = cv2.GaussianBlur(hsv_v, (nkernelSize, nkernelSize), 0)
    v_log = cv2.log(hsv_v)
    v_blur_log = cv2.log(v_blur)
    r_part_log = v_log - v_blur_log
    r_part = cv2.exp(r_part_log)
    r_part = cv2.convertScaleAbs(r_part, alpha = mean_illumination)
    r_part_32F = r_part.astype(np.float32)
    r_part_32F -= ADJUST_DELTA
    return r_part_32F


def calMeanVal(color_img, roi_x, roi_y, roi_width, roi_height):
    if color_img is None:
        return None
    color_img_32F = color_img.astype(np.float32)
    hsv_img = cv2.cvtColor(color_img_32F, cv2.COLOR_BGR2HSV)
    hsv_split = cv2.split(hsv_img)
    hsv_v = hsv_split[2]
    if isRoiLegal(hsv_v.shape[0], hsv_v.shape[1], roi_x, roi_y, roi_width, roi_height):
        hsv_v_roi = hsv_v[roi_x : roi_x + roi_width, roi_y : roi_y + roi_height]
    else:
        hsv_v_roi = hsv_v
    meanVal = hsv_v_roi.sum() / (hsv_v_roi.shape[0] * hsv_v_roi.shape[1])
    return meanVal


def isRoiLegal(img_width, img_height, roi_x, roi_y, roi_width, roi_height):
    return not (roi_x < 0 or roi_y < 0 or roi_width <= 0 or roi_height <= 0 or
            (roi_x + roi_width >=  img_width) or (roi_y + roi_height >= img_height))



if __name__ == "__main__":
    image = cv2.imread("D:/car_image_test/rgb_image_0.jpg")
    #cv2.imwrite("D:/car_image_test/rgb_image_0_SSR.jpg", retinex_ssr(image, 21, 100))
    #cv2.imwrite("D:/car_image_test/rgb_image_0_MSR.jpg", retinex_msr(image, 15, 81, 201, 100))
    #cv2.imshow("illu", retinex_ssr(image, 21, 100))
    cv2.imshow("illu", retinex_msr(image, 15, 81, 201, 100, 10))
    # calMeanVal(image, 5, 5, 50, 50)
    #cv2.imshow("adjust", adjustMeanVal(image, 788, 462, 20, 20, 30))
    cv2.waitKey(0)
