import os
import cv2
import numpy as np
from libs.dir_and_filename_info import get_dir_file_list


def cal_rgb_mean(images_list, pic_path, dest_file=''):
    total_color = np.array([0, 0, 0])
    
    for filename in images_list:
        img = cv2.imread(os.path.join(pic_path, filename))
        avg_color = np.mean(img, axis=(0,1))
        total_color = total_color + np.array(avg_color)

    avg_bgr = total_color / len(images_list)
    avg_rgb = avg_bgr[...,::-1]
    
    if dest_file:
        with open(dest_file, 'w') as file:
            file.write('%s' % list(avg_rgb))
    return avg_rgb


def compute_rgb_mean(src_path):
    dir_list, file_list = get_dir_file_list(src_path)
    sum_avgs = []
    if len(file_list) > 0:
        file_rgb = cal_rgb_mean(file_list, src_path, dest_file='')
        sum_avgs.append(file_rgb)

    for sub_dir in dir_list:
        sub_path = os.path.join(src_path, sub_dir)
        sum_avgs.extend(compute_rgb_mean(sub_path))
    return sum_avgs


def compute_and_save_rgb_mean(src_path, dest_path):
    sum_avgs = compute_rgb_mean(src_path)
    # print('sum avgs', sum_avgs)
    mean_avg = np.mean(sum_avgs, axis=0)
    dest_file_path = os.path.join(dest_path, '%s_rgb_mean.txt'%(os.path.basename(src_path)))
    with open(dest_file_path, 'w') as file:
        file.write('%s' % str(list(mean_avg)))
    print('rgb mean saved at %s' % dest_file_path)


if __name__ == '__main__':
    src_path = '/home/mechmind045/3d_data/rgbd_scans/mini_depth/train'
    compute_and_save_rgb_mean(src_path, os.path.dirname(src_path))

