# import the necessary packages
import argparse
import cv2
import numpy as np
import os
 
# initialize the list of reference points and boolean indicating
# whether cropping is being performed or not
refPt = []
refColor = [216,94,82]
cropping = False
 
def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global refPt, cropping, refColor
 
    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True
 
    # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append((x, y))
        cropping = False
 
        # draw a rectangle around the region of interest
        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("image", image)
    
    elif event == cv2.EVENT_MBUTTONDOWN:
        refColor = image[x,y]
        print("picking up color",refColor)
        
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--dir", required=True, help="Path to the image folder")
ap.add_argument("-d", "--dst", required=True, help="Path to the output folder")
args = vars(ap.parse_args())
 
# load the image, clone it, and setup the mouse callback function
files = os.listdir(args["dir"])
print()
image = cv2.imread(os.path.join(args["dir"],files[0]))
clone = image.copy()
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)
 
# keep looping until the 'q' key is pressed
while True:
    # display the image and wait for a keypress
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF
 
    # if the 'r' key is pressed, reset the cropping region
    if key == ord("r"):
        image = clone.copy()
 
    # if the 'c' key is pressed, break from the loop
    elif key == ord("c"):
        break
 
# if there are two reference points, then crop the region of interest
# from teh image and display it
# if len(refPt) == 2:
#     blank_image = np.zeros((image.shape[0],image.shape[1],3),np.uint8)
#     blank_image[:,:] = refColor
#     blank_image[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]] = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
#     cv2.imshow("fill color outside roi", blank_image)
#     cv2.waitKey(0)
 
# close all open windows
#cv2.destroyAllWindows()

print(files)
for file in files:
    image = cv2.imread(os.path.join(args["dir"],file))
    blank_image = np.zeros((image.shape[0],image.shape[1],3),np.uint8)
    blank_image[:,:] = refColor
    blank_image[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]] = image[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
    print(file)
    cv2.imwrite(os.path.join(args['dst'],file),blank_image)
    
    