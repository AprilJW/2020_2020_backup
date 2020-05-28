## cityscapes_format
This module implements a software tool for generating cityscape dataset based on .png file and .pickle file generated
from dataGen

### Demo
1. Modify simulation parameters in all config.yml files if required.
2. run setup_cityscape.py
'''shell
$ cd /path/to/repo/cityscapes_format
$ python setup_cityscape.py
'''
3. The generated data can be found in the folder as specified by output_path/result_path in /path/to/repo/config.yml .

### Output
1. original .png image file in cityscape_path/leftImg8bit.
2. .json file and segmenation mask images in cityscape_path/gtFine

### Parameters
the example cfg files contain the parameters of simulation.
```shell
cityscape_path: relative/path/to/cityscape/from/output_path
pickle_path: relative/path/to/pickle/from/output_path
sub_dirs: {'leftImg8bit': {'test':{'aachen':{}}, 'train':{'aachen':{}}, 'val':{'aachen':{}}}, 'imglists':{}, 'gtFine':{'test':{'aachen':{}}, 'train':{'aachen':{}}, 'val':{'aachen':{}}}}
set_dirs: {'test':{'aachen':{}}, 'train':{'aachen':{}}, 'val':{'aachen':{}}}
objectIDs: {'item1':'000019', 'item2':'000019', 'item3':'000019',...}
assignment:
    test: ['(.*)0','(.*)1','(.*)2']
    train: ['(.*)3','(.*)4','(.*)5','(.*)6','(.*)7']
    val: ['(.*)8','(.*)9']

```
