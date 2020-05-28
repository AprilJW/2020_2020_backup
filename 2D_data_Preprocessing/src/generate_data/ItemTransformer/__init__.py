from generate_data.ItemTransformer.Resize import Resize
from generate_data.ItemTransformer.Brightness import Brightness
from generate_data.ItemTransformer.Contrast import Contrast
from generate_data.ItemTransformer.HueTune import HueTune
from generate_data.ItemTransformer.Move import Move
from generate_data.ItemTransformer.RandomHighLight import RandomHighLight
from generate_data.ItemTransformer.Rotation import Rotation
from generate_data.ItemTransformer.Shadow import Shadow
from generate_data.ItemTransformer.Distortion import Distortion
from generate_data.ItemTransformer.Crop import Crop

operator_type_to_operator = {Resize.type: Resize, Brightness.type: Brightness, Contrast.type: Contrast,
                             HueTune.type: HueTune, Move.type: Move, RandomHighLight.type: RandomHighLight,
                             Rotation.type: Rotation, Shadow.type: Shadow, Distortion.type: Distortion, Crop.type: Crop}
