## voc_format
This module implements a software tool for generating Visual Object Classes (VOC) dataset based on .png file generated from dataGen
The images are required to be 500 × 500 pixels resolution

### Demo
1. Modify simulation parameters in all config.json files if required.

### Output
1. original .jpg image file in voc_path/JPEGImages.
2. .png instance label images in voc_path/SegmentationClassAug
3. .png pallete label images in voc_path/SegmentationClass

### Parameters
the example cfg files contain the parameters of simulation.
