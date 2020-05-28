import os
import copy
import shutil

from generate_data import  generate_helper

from util.auto_test_helper import create_data_generator, create_generator_config, random_load_seed,save_config
from util import util


seed_dir = "D:/data/2d_auto_test/seed"
target_dir = "D:/data/2d_auto_test/result"
bg_dir = "D:/data/2d_auto_test/bg"

generator_name_to_inputs = {}
data_generators = []  


if __name__ == "__main__":
    num = 1
    while True:
        sub_target_dir = os.path.join(target_dir,str(num))
        random_load_seed(seed_dir, sub_target_dir)
             
        data_generator ,random_settings = create_data_generator(bg_dir)
        data_generators.append(copy.deepcopy(data_generator))
        
        generate_config = create_generator_config(random_settings)
        generator_name_to_inputs[data_generator.name] = copy.deepcopy(generate_config)
    
        save_config(target_dir=sub_target_dir,data_generators=data_generators, generator_name_to_inputs=generator_name_to_inputs)
        
        generate_helper.generate_parallel(dest_path=sub_target_dir, prefix='2007_', 
                                          generator_name_to_inputs=generator_name_to_inputs, 
                                          data_generators=data_generators, 
                                          is_singleprocessing=False)
         
        expected_image_num = util.get_expected_image_num(configs=generator_name_to_inputs)    
        is_equal, actual_image_num = util.check_image_num(dir_path= sub_target_dir, generate_image_num=expected_image_num)
        if is_equal:
            shutil.rmtree(sub_target_dir)
            data_generators.clear()
            generator_name_to_inputs.clear()
            num+=1
        else:
            print("The number of images does not match the expected value, expect", expected_image_num, 'actual',actual_image_num)
            break
    
    
    