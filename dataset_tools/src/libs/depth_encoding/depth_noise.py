import numpy as np
import cv2
import math
import time
from libs.depth_encoding.exr_to_jpg import cvt_to_8uc1
from libs.depth_encoding.perlin_noise import generate_perlin_noise, generate_gauss_noise, rand_turbulence


def read_depth_image(depth_image_file):
    rgbf_ori = cv2.imread(depth_image_file, cv2.IMREAD_UNCHANGED)
    rgbf_ori = np.clip(rgbf_ori * 1000, 0.0, 65535.0)
    rgbf_ori = cv2.cvtColor(rgbf_ori, cv2.COLOR_BGR2GRAY)
    return rgbf_ori


def randomize_points(img, scale=1, ksize=5):
    edge_points_locs = np.where(img > 0)
    new_locs = []
    new_loc_x = np.array(list(map(lambda x: min(np.random.normal(x, scale=scale), img.shape[1]-1),
                                  edge_points_locs[0])))
    new_locs.append(new_loc_x.astype(int))
    new_loc_y = np.array(list(map(lambda x: min(np.random.normal(x, scale=scale), img.shape[0]-1),
                                  edge_points_locs[1])))
    new_locs.append(new_loc_y.astype(int))
    img_noise = np.zeros_like(img)
    img_noise[tuple(new_locs)] = 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    img_noise = cv2.morphologyEx(img_noise, cv2.MORPH_CLOSE, kernel)
    return img_noise


def randomize_contour(img, scale=1):
    _, cnts, hier = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # cv2.imshow('b', img)
    for i in range(len(cnts)):
        for j in range(len(cnts[i])):
            cnts[i][j][0][0] = min(
                np.random.normal(
                    loc=cnts[i][j][0][0],
                    scale=scale),
                img.shape[1])
            cnts[i][j][0][1] = min(
                np.random.normal(
                    loc=cnts[i][j][0][1],
                    scale=scale),
                img.shape[0])
    img_noise = np.zeros_like(img)
    cv2.drawContours(img_noise, cnts, -1, 255, cv2.FILLED, cv2.LINE_8, hier, 2)
    # cv2.imshow('e', img_noise)
    return img_noise


def get_blackhat(img, ksize=3):
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (ksize, ksize))
    blackhat_img = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)
    blackhat_img = randomize_points(blackhat_img, scale=2, ksize=ksize)
    _, cnts, hier = cv2.findContours(blackhat_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for cnt in cnts:
        if cv2.contourArea(cnt) > 200:
            cv2.drawContours(blackhat_img, [cnt], 0, 0, cv2.FILLED)
    return blackhat_img


def mark_shadow_line(rgbf_height, line_points, theta_tan, shadow_marker):
    if np.sum(rgbf_height[line_points[1], line_points[0]]) < 1:
        return

    shadower_height = rgbf_height[line_points[1][0]][line_points[0][0]]
    shadower_loc = line_points[:][0]
    for i in range(1, len(line_points[0])):
        shadowee_height = rgbf_height[line_points[1][i]][line_points[0][i]]
        height_diff = shadower_height - shadowee_height
        if height_diff > 0:
            shadow_width = theta_tan * (height_diff)
            # shadow_width *= np.random.normal(1, 0.01, size=None)
            if shadow_width > line_points[0][i] - shadower_loc[0]:
                shadow_marker[line_points[1][i]][line_points[0][i]] = 255
            else:
                shadower_height = shadowee_height
                shadower_loc = line_points[:, i]
        else:
            shadower_height = shadowee_height
            shadower_loc = line_points[:, i]


def get_line_points(image_shape, x_anchor, y_anchor, alpha_tan):
    line_points = [[x_anchor], [y_anchor]]
    if alpha_tan < 1.0:
        if alpha_tan < 0.001:
            new_points = np.array(
                list(map(lambda p: [p, y_anchor], range(x_anchor + 1, image_shape[1]))))
        else:
            alpha_cot = 1 / alpha_tan
            x_end = min(int(alpha_cot * (image_shape[0] - y_anchor) - x_anchor), image_shape[1])
            new_points = np.array(list(map(lambda p: [p, alpha_tan * (p - x_anchor) + y_anchor],
                                           range(x_anchor + 1, x_end))))
    else:
        if alpha_tan > 1000:
            new_points = np.array(
                list(map(lambda p: [x_anchor, p], range(y_anchor + 1, image_shape[0]))))
        else:
            y_end = min(int(alpha_tan * (image_shape[1] - x_anchor) + y_anchor), image_shape[0])
            alpha_cot = 1 / alpha_tan
            new_points = np.array(list(map(lambda p: [alpha_cot * (p - y_anchor) - x_anchor, p],
                                           range(y_anchor + 1, y_end))))

    line_points[0].extend(new_points[:, 0])
    line_points[1].extend(new_points[:, 1])
    return np.array(line_points).astype(int)


def mark_shadow(rgbf_height, alpha_tan, theta_tan):
    shadow_marker = np.zeros(rgbf_height.shape, np.uint8)

    if alpha_tan > 0.001:
        for x_anchor in range(rgbf_height.shape[1] - 1, -1, -1):
            y_anchor = 0
            line_points = get_line_points(rgbf_height.shape, x_anchor, y_anchor, alpha_tan)
            mark_shadow_line(rgbf_height, line_points, theta_tan, shadow_marker)

    if alpha_tan < 1000:
        for y_anchor in range(0, rgbf_height.shape[0]):
            x_anchor = 0
            line_points = get_line_points(rgbf_height.shape, x_anchor, y_anchor, alpha_tan)
            mark_shadow_line(rgbf_height, line_points, theta_tan, shadow_marker)
    return shadow_marker


def extract_sharp_slope(rgb8_depth):
    grad_sobel_x = cv2.Sobel(rgb8_depth, cv2.CV_8U, 1, 0)
    grad_sobel_x = cv2.convertScaleAbs(grad_sobel_x)
    _, grad_sobel_x = cv2.threshold(grad_sobel_x, 10, 255, cv2.THRESH_BINARY)
    grad_sobel_y = cv2.Sobel(rgb8_depth, cv2.CV_8U, 0, 1)
    grad_sobel_y = cv2.convertScaleAbs(grad_sobel_y)
    _, grad_sobel_y = cv2.threshold(grad_sobel_y, 10, 255, cv2.THRESH_BINARY)
    slope_marker = cv2.bitwise_or(grad_sobel_x, grad_sobel_y)
    return slope_marker


def extract_edges(rgb8_depth, thresh=100):
    grad_lap = cv2.Laplacian(rgb8_depth, cv2.CV_8U, ksize=5)
    grad_lap = cv2.convertScaleAbs(grad_lap)
    _, grad_lap = cv2.threshold(grad_lap, thresh, 255, cv2.THRESH_BINARY)
    return grad_lap


def add_noise_to_slope_marker(perlin_noise_img, slope_marker):
    slope_noise = cv2.bitwise_and(slope_marker, cv2.bitwise_not(perlin_noise_img))
    return slope_noise


def add_noise_to_shadow_marker(shadow_marker):
    # p_num = np.random.randint(15, 25)
    # gauss_points = [np.array(list(np.random.randint(0, len, p_num))) for len in shadow_marker.shape]
    # gauss = np.zeros_like(shadow_marker)
    # gauss[tuple(gauss_points)] = 255
    # ksize = 11
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    # gauss = cv2.morphologyEx(gauss, cv2.MORPH_DILATE, kernel)
    # shadow_noise = cv2.bitwise_and(shadow_marker, cv2.bitwise_not(gauss))
    # shadow_erode = cv2.erode(shadow_marker.copy(), np.ones((11, 11), np.uint8), iterations=1)
    # shadow_noise = cv2.bitwise_or(shadow_noise, shadow_erode)
    # cv2.imshow('b', shadow_noise)
    # shadow_noise = randomize_points(shadow_marker)
    # cv2.imshow('e', shadow_noise_edge)
    shadow_noise = randomize_contour(shadow_marker)
    ksize = 3
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    shadow_noise = cv2.morphologyEx(shadow_noise, cv2.MORPH_DILATE, kernel)
    # cv2.imshow('s', shadow_noise)
    return shadow_noise


def add_noise_to_edges_marker(edge_marker):
    edge_blackhat = get_blackhat(edge_marker, ksize=7)
    # edge_noise = perlin_noisy(edge_marker.shape, 100, 0, 8)
    edge_noise = randomize_points(edge_marker)
    ksize = 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    edge_noise = cv2.morphologyEx(edge_noise, cv2.MORPH_ERODE, kernel)
    edge_noise = cv2.bitwise_or(edge_noise, edge_blackhat)
    # cv2.imshow('hat', edge_noise)
    edge_dilate = cv2.dilate(edge_marker, np.ones((7, 7), np.uint8), iterations=1)
    gauss = generate_gauss_noise(edge_dilate.shape, 0.1)
    gauss = cv2.bitwise_and(edge_dilate, gauss.astype(np.uint8))
    edge_noise = cv2.bitwise_xor(edge_noise, gauss)
    # kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
    # edge_noise = cv2.dilate(edge_noise, kernel, iterations=1)
    return edge_noise


def add_slope_noise(rgb8_depth, perlin_noise_img, rgb8_noise):
    slope_marker = extract_sharp_slope(rgb8_depth)
    # cv2.imshow('slope marker', slope_marker)
    slope_noise = add_noise_to_slope_marker(perlin_noise_img, slope_marker)
    # cv2.imshow('slope noise', slope_noise)
    rgb8_noise[slope_noise > 0] = 0
    # cv2.imshow('image slope', rgb8_noise)


def add_shadow_noise(rgbf_depth, rgb8_noise):
    """
    :param rgbf_depth: raw depth image
    :param rgb8_noise: final noisy img need to update
    :return:
    """
    rgbf_height = np.max(rgbf_depth) - rgbf_depth
    theta_tan = math.tan(math.radians(15))
    alpha_tan = math.tan(math.radians(0))
    shadow_marker = mark_shadow(rgbf_height, alpha_tan, theta_tan)
    # cv2.imshow('shadow marker', shadow_marker)
    shadow_noise = add_noise_to_shadow_marker(shadow_marker)
    # cv2.imshow('shadow noise', shadow_noise)
    rgb8_noise[shadow_noise > 0] = 0
    # cv2.imshow('image shadow', rgb8_noise)

    return shadow_marker


def add_edge_noise(rgb8_depth, rgb8_noise):
    edge_marker = extract_edges(rgb8_depth)
    # cv2.imshow('edge marker', edge_marker)
    edge_noise = add_noise_to_edges_marker(edge_marker)
    # cv2.imshow('edge noise', edge_noise)
    rgb8_noise[edge_noise > 0] = 0
    # cv2.imshow('image edge', rgb8_noise)


def add_noise_to_bg_marker(perlin_noise_img, bg_marker):
    bg_noise = cv2.bitwise_and(bg_marker, cv2.bitwise_not(perlin_noise_img))
    return bg_noise


def extract_background(rgb8_depth):
    _, bg_marker = cv2.threshold(rgb8_depth, 253, 255, cv2.THRESH_BINARY)
    return bg_marker


def add_background_noise(rgb8_depth, perlin_noise_img, rgb8_noise):
    bg_marker = extract_background(rgb8_depth)
    # cv2.imshow('bg marker', bg_marker)
    bg_noise = add_noise_to_bg_marker(perlin_noise_img, bg_marker)
    # cv2.imshow('bg noise', bg_noise)
    rgb8_noise[bg_noise > 0] = 0
    # cv2.imshow('image bg', rgb8_noise)


def depth_noisy(depth_image_file, cvt_method=[-1, 1]):
    rgbf_depth = read_depth_image(depth_image_file)
    rgb8_depth = cvt_to_8uc1(rgbf_depth, cvt_method=cvt_method)
    # cv2.imwrite(os.path.join(src_path, filename + '.jpg'), rgb8_depth)
    # begin = time.time()
    rgb8_noise = rgb8_depth.copy()

    noise_factor = generate_perlin_noise(rgb8_depth.shape)
    perlin_noise_img = rand_turbulence(noise_factor, 0, 100, 8)

    # end = time.time()
    # print('perlin noise in {} seconds'.format(end - begin))
    # begin = time.time()
    add_background_noise(rgb8_depth, perlin_noise_img, rgb8_noise)

    # end = time.time()
    # print('bg noise in {} seconds'.format(end - begin))
    # begin = time.time()
    add_slope_noise(rgb8_depth, perlin_noise_img, rgb8_noise)

    # end = time.time()
    # print('slope noise in {} seconds'.format(end - begin))
    # begin = time.time()
    add_shadow_noise(rgbf_depth, rgb8_noise)

    # end = time.time()
    # print('shadow noise in {} seconds'.format(end - begin))
    # begin = time.time()
    add_edge_noise(rgb8_depth, rgb8_noise)

    # cv2.waitKey(0)
    # end = time.time()
    # print('edge in {} seconds'.format(end - begin))
    # cv2.imwrite(os.path.join(src_path, filename + '_noise.jpg'), rgb8_noise)
    return rgb8_noise


if __name__ == '__main__':
    import os
    src_path = '/home/mechmind021/3d_data/sf_boxes/depth'
    files = sorted(os.listdir(src_path))
    for filename in files:
        if filename.endswith('.exr'):
            print(filename)
            depth_image_file = os.path.join(src_path, filename)
            depth_noisy(depth_image_file)
