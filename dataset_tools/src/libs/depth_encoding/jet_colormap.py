import cv2

def apply_jet_mapping(image_depth):
    image_color = cv2.applyColorMap(image_depth, cv2.COLORMAP_JET)
    return image_color