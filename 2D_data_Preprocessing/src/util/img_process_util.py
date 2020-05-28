import os
import sys
import math

import numpy as np
import cv2

img_type = ['.bmp', '.jpg', '.png', '.tiff']
is_regression_test = False


def crop_image_roi(image, roi):
    """
    :param image: 1-channel image
    :param roi: in x,y,w,h
    :return: croped image
    """
    return image[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]


def intersection(ai, bi):
    """
    :param ai:  [x1, y1, x2, y2]
    :param bi: [x1, y1, x2, y2]
    :return: intersection area
    """
    x = max(ai[0], bi[0])
    y = max(ai[1], bi[1])
    w = min(ai[2], bi[2]) - x
    h = min(ai[3], bi[3]) - y
    if w < 0 or h < 0:
        return 0
    return w * h


def bndbox_area(bndbox):
    """
    :param bndbox: [x1, y1, x2, y2]
    :return:
    """
    return (bndbox[2] - bndbox[0]) * (bndbox[3] - bndbox[1])


def extend_canvas(image_bgra, bndboxes, border_top=-1, border_bottom=-1, border_left=-1, border_right=-1, color=0):
    """
    extend image with len = max(min(image_width /4, image_height /4),100), find largest bounding box extend same size
    :param image_bgra: image in 4-channel
    :param bndboxes: roi bndboxes in [x1,y1,x2,y2]
    :param border_top: using default border_length if is -1
    :param border_bottom: using default border_length if is -1
    :param border_left: using default border_length if is -1
    :param border_right: using default border_length if is -1
    :param color: border color default 0
    :return: image extended and largest bounding box extended
    """
    border_len = max(int(min(image_bgra.shape[:2]) / 4), 100)
    border_top = border_len if border_top == -1 else border_top
    border_bottom = border_len if border_bottom == -1 else border_bottom
    border_left = border_len if border_left == -1 else border_left
    border_right = border_len if border_right == -1 else border_right

    img_larger_canvas = cv2.copyMakeBorder(image_bgra, top=border_top, bottom=border_bottom, left=border_left,
                                           right=border_right, borderType=cv2.BORDER_CONSTANT,
                                           value=color)
    if len(bndboxes) == 0:
        return

    largest_bndbox = bndboxes[0].copy()
    for bbox in bndboxes:
        if bndbox_area(bbox) > bndbox_area(largest_bndbox):
            largest_bndbox = bbox.copy()

    bndbox = [border_left + largest_bndbox[0], border_top + largest_bndbox[1],
              border_left + largest_bndbox[2], border_top + largest_bndbox[3], largest_bndbox[4]]

    return img_larger_canvas, bndbox


def dilate_image(bin_image, ksize=5, keep_size=True):
    """
       1.dilate image
       2.erode image if keep_size is true
    :param bin_image:
    :param ksize: morph kernel size
    :param keep_size:
    :return: image
    """
    border_len = max(int(min(bin_image.shape[:2]) / 4), 100)
    img_binary = bin_image.copy()
    large_img_binary = cv2.copyMakeBorder(img_binary, top=border_len, bottom=border_len, left=border_len,
                                          right=border_len, borderType=cv2.BORDER_CONSTANT,
                                          value=0)

    large_img_binary = cv2.dilate(large_img_binary, np.ones((ksize, ksize), np.uint8))  # connect main parts
    if keep_size:
        large_img_binary = cv2.erode(large_img_binary, np.ones((ksize, ksize), np.uint8))

    img_binary = large_img_binary[border_len:(border_len + img_binary.shape[0]),
                 border_len:(border_len + img_binary.shape[1])]

    return img_binary


def get_roi_mask(img, is_object_range, hsv_range, bgr_range):
    # noise reduction
    img_init = cv2.GaussianBlur(img, (5, 5), 0)

    if np.any(hsv_range):
        hsv_lower = np.array(hsv_range[0])
        hsv_upper = np.array(hsv_range[1])
        img_HSV = cv2.cvtColor(img_init, cv2.COLOR_BGR2HSV)
        obj_binary_hsv = cv2.inRange(img_HSV, hsv_lower, hsv_upper)
        if not is_object_range:
            obj_binary_hsv = cv2.bitwise_not(obj_binary_hsv)
    else:
        obj_binary_hsv = np.full((img_init.shape[0], img_init.shape[1], 1), 255, np.uint8)

    if np.any(bgr_range):
        obj_binary_bgr = cv2.inRange(img_init, np.array(bgr_range[0]), np.array(bgr_range[1]))
        if not is_object_range:
            obj_binary_bgr = cv2.bitwise_not(obj_binary_bgr)
    else:
        obj_binary_bgr = np.full((img_init.shape[0], img_init.shape[1], 1), 255, np.uint8)

    obj_binary = cv2.bitwise_and(obj_binary_hsv, obj_binary_bgr)
    img_binary = dilate_image(obj_binary)

    return img_binary


def get_objects_image_and_bndboxes(img_roi, is_object_range, hsv_range, bgr_range, has_holes, gta_bnd_boxes,
                                   overlap_min):
    """
        get mask in hsv range

        Args:
            img_roi: color image
            lowerHSV: hsv range lower
            upperHSV: hsv range upper
        Return:
            img_binary: mask image that color in HSV range,with bound box w,h in a fixed range
    """

    img_binary = get_roi_mask(img_roi, is_object_range, hsv_range, bgr_range)
    contours = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    bnd_boxes = []
    for contour in contours[1]:
        x, y, w, h = cv2.boundingRect(contour)
        bndbox = [x, y, x + w, y + h]

        if len(gta_bnd_boxes) == 0:
            bnd_boxes.append(bndbox)
            if not has_holes:
                cv2.drawContours(img_binary, [contour], 0, 255, cv2.FILLED)
        else:
            for gta_bnd_box in gta_bnd_boxes:
                intersection_area = intersection(gta_bnd_box, bndbox)
                area = (gta_bnd_box[2] - gta_bnd_box[0]) * (gta_bnd_box[3] - gta_bnd_box[1])
                if intersection_area / area > overlap_min:
                    for j in range(4, len(gta_bnd_box)):
                        bndbox.append(gta_bnd_box[j])
                    if not has_holes:
                        cv2.drawContours(img_binary, [contour], 0, 255, cv2.FILLED)

            if len(bndbox) == len(gta_bnd_boxes[0]):
                bnd_boxes.append(bndbox)

    # get mask image roi
    b, g, r = cv2.split(img_roi)
    img_BGRA = cv2.merge([b, g, r, img_binary], 4)
    # get src image roi

    return img_BGRA, bnd_boxes


def remove_img_background(img, background, thre):
    """
        subtraction of img and background

        Args:
            img: input image
            background: background
            thre: sub image threshold
        Return:
            img_remove: sub result in a binary image
    """
    img_sub = abs(img - background)
    img_sub = cv2.cvtColor(img_sub, cv2.COLOR_BGR2GRAY)
    ret, img_remove = cv2.threshold(img_sub, thre, 255, cv2.THRESH_BINARY)

    return img_remove


def random_noise_image(img_height, img_width):
    """
        generate a random noise image with 4-channel,alpha channel is zero

        Args:
            img_height: generate image height
            img_width: generate image width
        Return:
            result : 4-channel image,alpha channel is zero,b,g,r is random in [0,255]
    """
    bn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)
    gn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)
    rn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)
    alpha = np.zeros([img_height, img_width], np.uint8)
    result = cv2.merge([bn, gn, rn, alpha])
    return result


def image_show(name, img, color):
    bg = np.zeros(img.shape, np.uint8)
    bg.fill(color)
    img_show = paint_on(img, bg)
    cv2.imshow(name, img_show)
    while cv2.getWindowProperty(name, 0) >= 0:
        key = cv2.waitKey(100)  # change the value from the original 0 (wait forever) to something appropriate
        if key == 27 or key == 13:  # 'Esc' or 'Enter' key
            cv2.destroyWindow(name)
            break


def paint_on(img, background):
    """
        paint img on background
        Args:
            img: src image,4-channel,alpha channel is mask of foreground
            background: background for paint
        Return
            result
    """
    if img.shape[2] != 4 or img.shape != background.shape:
        return background

    bgra_img = cv2.split(img)
    bgra_bg = cv2.split(background)
    a_img = bgra_img[3]
    a_rev = cv2.bitwise_not(a_img)

    img_locs = np.where(a_img != 0)
    bgra_bg_new = bgra_bg.copy()

    for i in range(len(bgra_img) - 1):
        bg_part = np.multiply(bgra_bg[i][img_locs[0], img_locs[1]], a_rev[img_locs[0], img_locs[1]] / 255.0)
        img_part = np.multiply(bgra_img[i][img_locs[0], img_locs[1]], a_img[img_locs[0], img_locs[1]] / 255.0)
        bgra_bg_new[i][img_locs[0], img_locs[1]] = (bg_part + img_part).astype(np.uint8)
    bgra_bg_new[3] = cv2.bitwise_or(bgra_bg_new[3], bgra_img[3])

    return cv2.merge(bgra_bg_new)


def random_noise_background(img):
    """
        put img in random noise background
        Args:
            img: 4-channel image, alpha channel is foreground mask
        Return:
            3-channel image
    """
    if img.shape[2] != 4:
        return img
    bs, gs, rs, mask = cv2.split(img)
    mask_not = cv2.bitwise_not(mask)
    img_height = img.shape[0]
    img_width = img.shape[1]

    bn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)
    gn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)
    rn = np.random.randint(0, 255, size=(img_height, img_width)).astype(np.uint8)

    bresult = cv2.bitwise_or(cv2.bitwise_and(bn, mask_not), cv2.bitwise_and(bs, mask))
    gresult = cv2.bitwise_or(cv2.bitwise_and(gn, mask_not), cv2.bitwise_and(gs, mask))
    rresult = cv2.bitwise_or(cv2.bitwise_and(rn, mask_not), cv2.bitwise_and(rs, mask))

    result = cv2.merge([bresult, gresult, rresult])

    return result


def feather_edges(alpha, ksize=3, iterations=1):
    """
    feather edges
    using kernel like
    0 1/5 1/5
    1/5 0 1/5
    1/5 1/5 0
    :param alpha:  input image in 1-channel
    :param ksize: filter kernel size
    :param iterations:
    :return:
    """
    a_blur = cv2.pyrUp(alpha)
    a_blur = cv2.bitwise_not(a_blur)
    kernel = np.ones((ksize, ksize), np.float32) / (2 * ksize - 1)
    for i in range(ksize):
        kernel[i][i] = 0.0

    for i in range(iterations):
        a_blur = cv2.filter2D(a_blur, -1, kernel)
    a_blur = cv2.bitwise_not(a_blur)
    a_blur = cv2.pyrDown(a_blur)
    return a_blur


def erode_gauss_blur(alpha, ksize=3, iterations=1):
    a_blur = cv2.bitwise_not(alpha)
    for i in range(iterations):
        a_blur = cv2.GaussianBlur(a_blur, (ksize, ksize), sigmaX=0)
    a_blur = cv2.bitwise_not(a_blur)
    return a_blur


def blur_edges(alpha, ksize=3, iterations=1):
    """
    average filter
    :param alpha: input image in 1-channel
    :param ksize: filter kernel size
    :param iterations:
    :return: image
    """
    a_blur = cv2.pyrUp(alpha)
    # kernel = np.ones((ksize, ksize), np.float32)
    for i in range(iterations):
        a_blur = cv2.blur(a_blur, (ksize, ksize))
    a_blur = cv2.pyrDown(a_blur)
    return a_blur


def straighten_edges(alpha):
    # cv2.imwrite('/home/gwj/a.png', a)
    _, a = cv2.threshold(alpha, 128, 255, cv2.THRESH_BINARY)
    _, cnts, hier = cv2.findContours(a, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # straighten edges
    smoothened = []
    for cnt in cnts:
        epsilon = 0.001 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        smoothened.append(approx)
    a_smooth = np.zeros(a.shape, np.uint8)
    cv2.drawContours(a_smooth, smoothened, -1, 255, cv2.FILLED, cv2.LINE_8, hier)
    return a_smooth


def get_max_blob(bin_image, thre=0):
    """
        find max len contours blob in bin_image, paint on a new image
        Args:
            bin_image: binary image for picking blob
        Returns:
            max_contour: the max len contour point array
    """
    _, bin_img = cv2.threshold(bin_image, thre, 255, cv2.THRESH_BINARY)
    contours = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    max_len = 0
    max_contour = np.array([])
    for contour in contours[1]:
        if len(contour) > max_len:
            max_len = len(contour)
            max_contour = contour

    return max_contour


def get_max_blob_bin_image(max_contour, a_img, is_fill=True, line_width=7):
    """
        find max len contours blob in bin_image, paint on a new image

        Args:
            bin_image: binary image for picking blob
            is_fill: paint contours or fill contours
            line_width: contours line width if only paint contours
        Returns:
            img_main_contours: the max len contour blob image
            main_bnd_box: the max len contour blob bounding box
            max_contour: the max len contour point array
    """

    img_max_contour = np.zeros(a_img.shape, np.uint8)

    if len(max_contour) != 0:
        if not is_fill:
            cv2.drawContours(img_max_contour, [max_contour], 0, 255, line_width, cv2.LINE_8)
        else:
            cv2.drawContours(img_max_contour, [max_contour], 0, 255, cv2.FILLED)

    _, a = cv2.threshold(a_img, 0, 255, cv2.THRESH_BINARY)
    img_max_contour = cv2.bitwise_and(img_max_contour, a)
    return img_max_contour


def get_all_blob_bin_image(bin_image, is_fill=False, line_width=4):
    """
        paint all blob in input image on a new image

        Args:
            bin_image: binary image for picking blob
            is_fill: paint contours of fill contours
            line_width: contours line width if only paint contours
        Return:
            painted image
    """
    contours = get_all_blob_contours_in_bin_image(bin_image)
    img_contours = np.zeros(bin_image.shape, np.uint8)
    for contour in contours[1]:
        if not is_fill:
            cv2.drawContours(img_contours, [contour], 0, 255, line_width, cv2.LINE_8)
        else:
            cv2.drawContours(img_contours, [contour], 0, 255, cv2.FILLED)
    return img_contours


def get_all_blob_contours_in_bin_image(bin_image):
    _, bin_img = cv2.threshold(bin_image, 0, 255, cv2.THRESH_BINARY)
    contours = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    return contours


def get_all_external_contours_in_bin_image(bin_image):
    _, bin_img = cv2.threshold(bin_image, 0, 255, cv2.THRESH_BINARY)
    contours = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours


# to judge if the item truncated by other object
def if_truncated(bin_img):
    _, bin_img = cv2.threshold(bin_img, 128, 255, cv2.THRESH_BINARY)
    contours = get_all_external_contours_in_bin_image(bin_img.copy())
    contour_len = len(contours[1])
    # to substract the interference point from the total contour length
    for contour in contours[1]:
        if len(contour) < 10:
            contour_len -= 1
    # if the left contour length is more than one except the interference point, the object is truncated
    if contour_len > 1:
        return True
    return False


def calc_bndbox(image):
    """
        find max len contour in image and return it's bounding box
    :param image:
    :return:
    """
    _, _, _, a = cv2.split(image)
    contour = get_max_blob(a)
    bnd_box = cv2.boundingRect(contour)
    return [bnd_box[0], bnd_box[1], bnd_box[0] + bnd_box[2], bnd_box[1] + bnd_box[3]]


# return roi is xmin,ymin,xmax,ymax
def _get_roi_from_wh(roi_width, roi_height, img_width, img_height):
    return [(img_width - roi_width) / 2,
            (img_height - roi_height) / 2,
            (img_width - roi_width) / 2 + roi_width,
            (img_height - roi_height) / 2 + roi_height]


def _calculate_center_roi_min_and_max(roi_length, img_length):
    """
    given a roi size and image size, return coordinate of roi's left-top point, roi is in the center of image
    :param roi_length:
    :param img_length:
    :return:
    """
    return max(0, (img_length - roi_length) / 2), min((img_length - roi_length) / 2 + roi_length, img_length)


def _calculate_specific_roi_min_and_max(roi_origin_coordinate, roi_length, img_length):
    return max(0, ((roi_origin_coordinate + roi_length) < img_length) and roi_origin_coordinate or (
            img_length - roi_length)), \
           min(roi_origin_coordinate + roi_length, img_length)


def find_max_contour_according_to_bndbox(img):
    """

    :param img:
    :return:
    """
    img_dilate = cv2.dilate(img, np.ones((5, 5), np.uint8), 1)
    _, cnts, _ = cv2.findContours(img_dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if cnts is not None and len(cnts) > 0:
        max_cnt = []
        max_bbox = 0
        max_id = -1
        for idx, cnt in enumerate(cnts):
            bnd_box = cv2.boundingRect(cnt)
            if bnd_box[2] * bnd_box[3] > max_bbox:
                max_cnt = cnt.copy()
                max_bbox = bnd_box[2] * bnd_box[3]
                max_id = idx

        if max_bbox > 0:
            cv2.drawContours(img_dilate, [max_cnt], 0, 255, cv2.FILLED)
            cnts.pop(max_id)

        for cnt in cnts:
            cv2.drawContours(img_dilate, [cnt], 0, 0, cv2.FILLED)
        img = cv2.erode(img_dilate, np.ones((10, 10), np.uint8), 1)
        img = cv2.dilate(img, np.ones((5, 5), np.uint8), 1)

    return img


def floodFill(seed_x, seed_y, im, mount_thre):
    """
        flood fill with mount thresold in 4-direction
    :param seed_x: seed position
    :param seed_y: seed position
    :param im: image in 1-channel
    :param mount_thre: if im[x][y] <= mount_thre/2 this point mark as 255
    :return: image
    """
    im_height, im_width = im.shape[:2]
    sys.setrecursionlimit(im_height * im_width)
    to_fill = set()
    to_fill.add((seed_x, seed_y))
    while not len(to_fill) == 0:
        (x, y) = to_fill.pop()
        if im[y][x] > int(mount_thre / 2):
            continue
        im[y][x] = 255
        if x - 1 >= 0:
            to_fill.add((x - 1, y))
        if x + 1 < im_width:
            to_fill.add((x + 1, y))
        if y - 1 >= 0:
            to_fill.add((x, y - 1))
        if y + 1 < im_height:
            to_fill.add((x, y + 1))
    return im


def fill_holes(mask, ksize=5):
    """
      morph_close opt on mask image with kernel size default 5,paint each contours with 0 on new image
    :param mask:  input image in 1-channel
    :param ksize: kernel size
    :return:
    """
    kernel = np.ones((ksize, ksize), np.uint8)
    new_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    _, contour, _ = cv2.findContours(new_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contour:
        cv2.drawContours(new_mask, [cnt], 0, 255, -1)
    return new_mask


def fit_image_to_size(img=None, target_width=0, target_height=0, fill_color=None):
    """
        resize image to given size, keep origin aspect ratio padding with fill_color
    :param img: input image
    :param target_width:
    :param target_height:
    :param fill_color: same depth with input image
    :return:
    """
    left_border = right_border = top_border = bottom_border = 0
    width = img.shape[1]
    height = img.shape[0]
    if width / height > target_width / target_height:
        delta_height = target_height * width / target_width - height
        top_border = int(math.floor(delta_height / 2))
        bottom_border = int(math.ceil(delta_height / 2))
    elif width / height < target_width / target_height:
        delta_width = target_width * height / target_height - width
        left_border = int(math.floor(delta_width / 2))
        right_border = int(math.ceil(delta_width / 2))
    img = cv2.copyMakeBorder(img, top=top_border, bottom=bottom_border, left=left_border,
                             right=right_border, borderType=cv2.BORDER_CONSTANT,
                             value=fill_color)
    img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
    return img


def get_high_light_mask(im_height, im_width, mount_range=50):
    """
        generate random image, flood fill with random seed where value less than mount range/5
    :param im_height:
    :param im_width:
    :param mount_range:
    :return:
    """
    im = np.random.randint(mount_range, size=(im_height, im_width))
    xs, ys = np.where(im <= int(mount_range / 5))
    idx = np.random.randint(0, len(xs))
    x = xs[idx]
    y = ys[idx]
    mask = floodFill(x, y, im, mount_range)
    new_im = np.where(mask < 255, 0, 255).astype('uint8')
    return new_im


def check_area(mask, min_area=10, max_area=1000):
    """
    checn first external contour area in range min_area,max_area
    this function is not capabel to deal with mask contains 2 or more contours
    :param mask:
    :param min_area:
    :param max_area:
    :return:
    """
    _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) > 0:
        area = cv2.contourArea(contours[0])
        if area > min_area and area < max_area:
            return True
        else:
            return False
    else:
        return False


def is_image_file(path):
    """
        is a file perfix in image type list
    :param path:
    :return:
    """
    return os.path.splitext(path)[-1] in img_type


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
    return [[float(rot_box[0][0]), float(rot_box[0][1])], [float(wh_idx[1][0]), float(wh_idx[0][0])], float(
        -theta * 180 / np.pi)]
