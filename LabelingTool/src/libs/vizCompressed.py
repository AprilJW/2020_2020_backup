from PyQt5.QtCore import QFile,qUncompress
import cv2
import os
from fileinput import filename

def vizCompressed(fileName):
    #fileName = 'D:/Data/10_23_shunfengmix/rgb_image_58'
    
    filenamesplit = os.path.splitext(filename)
    print("file name:", filenamesplit)
    file = QFile(filenamesplit[0]+'.compressed')
    file.open(QFile.ReadOnly)
    if file.isOpen():
        data = file.readAll()
        labels = qUncompress(data)
    img = cv2.imread(filenamesplit[0]+'.jpg')
    
    for r in range(img.shape[0]):
        for c in range(img.shape[1]):
            index = r * img.shape[1] + c
            if(labels[index] == '1'):#tape
                img[r,c] = [0,0,255]
            elif(labels[index] == '2'):#boundry
                img[r,c] = [0,165,255]
            elif(labels[index] != '0'):#exception
                img[r,c] = [255,255,0]
    
    
    cv2.imshow('image',img)
    cv2.waitKey(0)
    cv2.imwrite(filenamesplit[0]+'_rf.jpg',img)

