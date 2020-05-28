import os
import cv2
import numpy as np

def calcMeanRgb(img_path, save_path):
    img_list = os.listdir(img_path)
    b_value, g_value, r_value = 0, 0, 0
    img_num = len(img_list)
    for img_name in img_list:
        b,g,r = cv2.split(cv2.imread(os.path.join(img_path, img_name)))
        b_value += np.mean(b)
        g_value += np.mean(g)
        r_value += np.mean(r)
    b_mean = b_value / img_num
    g_mean = g_value / img_num
    r_mean = r_value / img_num
    if not save_path.endswith(".txt"):
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        save_path = os.path.join(save_path,"mean_rgb.txt")
    with open(save_path, "w+") as f:
        f.write("b: {}\tg: {}\tr: {}".format(b_mean, g_mean, r_mean))



if __name__ == "__main__":
    calcMeanRgb(r"C:\Users\mech-mind-024\Desktop\imgTest", r"C:\Users\mech-mind-024\Desktop")