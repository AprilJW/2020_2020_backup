import os
import cv2
import numpy as np
from PIL import Image
from optparse import OptionParser
import copy
import sys

def floodFill(x,y,im,mount_range):
    im_height,im_width = im.shape[:2]
    sys.setrecursionlimit(max(im_height,im_width))
    toFill = set()
    toFill.add((x,y))
    while not len(toFill)==0:
        (x,y) = toFill.pop()
        single_pixel = im[y][x]
        if single_pixel > int(mount_range/2):
            continue
        im[y][x] = 255
        if x-1>=0:
            toFill.add((x-1,y))
        if x+1<im_width:
            toFill.add((x+1,y))
        if y-1>=0:
            toFill.add((x,y-1))
        if y+1<im_height:
            toFill.add((x,y+1))
    return im

def Laplacian_Pyramid_Blending_with_mask(A, B, m, num_levels = 5):
    # assume mask is float32 [0,1]

    # generate Gaussian pyramid for A,B and mask
    GA = A.copy()
    GB = B.copy()
    GM = m.copy()
    gpA = [GA]
    gpB = [GB]
    gpM = [GM]
    for i in range(num_levels):
        GA = cv2.pyrDown(GA)
        GB = cv2.pyrDown(GB)
        GM = cv2.pyrDown(GM)
        gpA.append(np.float32(GA))
        gpB.append(np.float32(GB))
        gpM.append(np.float32(GM))
    # generate Laplacian Pyramids for A,B and masks
    lpA  = [gpA[num_levels-1]] # the bottom of the Lap-pyr holds the last (smallest) Gauss level
    lpB  = [gpB[num_levels-1]]
    gpMr = [gpM[num_levels-1]]
    for i in range(num_levels-1,0,-1):
        # Laplacian: subtarct upscaled version of lower level from current level
        # to get the high frequencies
        size = (gpA[i-1].shape[1],gpA[i-1].shape[0])
        LA = np.subtract(gpA[i-1], cv2.pyrUp(gpA[i],dstsize=size))
        LB = np.subtract(gpB[i-1], cv2.pyrUp(gpB[i],dstsize=size))
        lpA.append(LA)
        lpB.append(LB)
        gpMr.append(gpM[i-1]) # also reverse the masks

    # Now blend images according to mask in each level
    LS = []
    for la,lb,gm in zip(lpA,lpB,gpMr):
        ls = la * gm + lb * (1.0 - gm)
        LS.append(ls)

    # now reconstruct
    ls_ = LS[0]
    for i in range(1,num_levels):
        size = (LS[i].shape[1],LS[i].shape[0])
        ls_ = cv2.pyrUp(ls_,dstsize=size)
        ls_ = np.add(ls_, LS[i]+np.ones(LS[i].shape)*6)

    return np.clip(ls_,0,255,out = ls_)

def fill_holes(mask):
    kernel = np.ones((5,5),np.uint8)
    new_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    _,contour,hier = cv2.findContours(new_mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contour:
        cv2.drawContours(new_mask,[cnt],0,255,-1)
    return new_mask

def get_high_light(im_height,im_width,mount_range):
    im = np.random.randint(mount_range,size = (im_height,im_width))
    x, y = np.random.randint(0,im_width-1), np.random.randint(0,im_height-1)
    while im[y][x]>int(mount_range/5):
        x, y = np.random.randint(0,im_width-1), np.random.randint(0,im_height-1)
    mask = floodFill(x, y, im, mount_range)
    new_im = np.where(mask<255,0,255).astype('uint8')
    return new_im
    
def check_area(mask,min_area=10,max_area=1000):
    _,contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    if len(contours)>0:
        area = cv2.contourArea(contours[0])
        if area>min_area and area < max_area:
            return True
        else:
            return False
    else:
        return False

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("--seed_path",dest = "seed_path", help="The path of seed.")
    parser.add_option("--seed_path_output",dest = "seed_path_output", help="The output path of seed augmented.")
    parser.add_option("--aug_times",dest = "aug_times", default = 20, help="The times for seed augmentation through adding highlight.")
    parser.add_option("--min_hl_num",dest = "min_hl_num", default = 0, help="The minimum number of highlight sources being added to a single seed.")
    parser.add_option("--max_hl_num",dest = "max_hl_num", default = 4, help="The maximum number of highlight sources being added to a single seed.")
    parser.add_option("--pyr_num",dest = "pyr_num", default = 2, help="The number of Pyramid layers.")
    parser.add_option("--min_hl_area",dest = "min_hl_area", default =50, help="The minimum area of single highlight.")
    parser.add_option("--max_hl_area",dest = "max_hl_area", default = 100, help="The maximum area of single highlight.")
    parser.add_option("--mount_range",dest = "mount_range", default = 50, help="The range of random moutain.")
    
    (options, args) = parser.parse_args()
    
    seed_path = options.seed_path
    seed_path_output = options.seed_path_output
    aug_times = int(options.aug_times)
    min_hl_num = int(options.min_hl_num)
    max_hl_num = int(options.max_hl_num)
    pyr_num = int(options.pyr_num)
    seed_path_output = options.seed_path_output
    min_hl_area = options.min_hl_area
    max_hl_area = options.max_hl_area
    mount_range = int(options.mount_range)
    
    MASK_PATH = r'C:\Users\mech-mind-024\Desktop\mask_durex'
    
    if not os.path.exists(seed_path_output):
        os.makedirs(seed_path_output)
    seed_list = os.listdir(seed_path)
    seed_num = len(seed_list)
    for seed_idx in range(seed_num):
        seed_name = seed_list[seed_idx]
        seed_rgba = cv2.imread(os.path.join(seed_path,seed_name),cv2.IMREAD_UNCHANGED)
        seed_rgb = seed_rgba[:,:,:3]
        seed_a = seed_rgba[:,:,-1]
        seed_height,seed_width = seed_rgba.shape[:2]
        sys.setrecursionlimit(max(seed_height,seed_width))
        for aug_time_idx in range(aug_times):
            new_seed_name = str(seed_idx*aug_times+aug_time_idx)+'.png'
            hl_num = np.random.randint(min_hl_num,max_hl_num)
            hl_b = np.zeros((seed_height,seed_width)).astype('uint8')
            hl_g = np.zeros((seed_height,seed_width)).astype('uint8')
            hl_r = np.zeros((seed_height,seed_width)).astype('uint8')
            for hl_index in range(hl_num):
                hl_mask = get_high_light(seed_height,seed_width,mount_range)
                while not check_area(hl_mask,min_area=min_hl_area,max_area=max_hl_area):
                    hl_mask = get_high_light(seed_height,seed_width,mount_range)
                hl_mask = fill_holes(hl_mask)
                hl_b = np.where((hl_mask>0)|(hl_b>0),np.random.randint(245,255),0)
                hl_g = np.where((hl_mask>0)|(hl_g>0),np.random.randint(245,255),0)
                hl_r = np.where((hl_mask>0)|(hl_r>0),np.random.randint(245,255),0)
            hl_rgb = cv2.merge((hl_b,hl_g,hl_r))
            seed_hl_mask = np.where(hl_rgb>0,seed_rgb,0)
            delta_mask = np.subtract(hl_rgb,seed_hl_mask)
            np.clip(delta_mask,0,255,out=delta_mask)
            delta_mask = cv2.blur(delta_mask,(5,5))
            noise_mask = np.random.normal(scale=2,size=delta_mask.shape).astype(np.int32)
            delta_mask = np.where(delta_mask>0,delta_mask+noise_mask,0)
#             cv2.imwrite(os.path.join(MASK_PATH,new_seed_name),hl_rgb.astype('uint8'))
            new_im = np.add(seed_rgb,delta_mask)
            np.clip(new_im,0,255,out = new_im)
            new_im = np.dstack((new_im,seed_a))
            cv2.imwrite(os.path.join(seed_path_output,new_seed_name),new_im)
