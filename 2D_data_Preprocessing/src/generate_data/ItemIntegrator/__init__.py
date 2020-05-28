from generate_data.ItemIntegrator.ItemBlender import ItemBlender
from generate_data.ItemIntegrator.ItemsToImage import ItemsToImage
from generate_data.ItemIntegrator.Background import ColorBackground, RandomNoiseBackground, FileBackground
from generate_data.ItemIntegrator.SeedItemPicker import SeedItemPicker
from generate_data.ItemIntegrator.UpdateGenerateNum import UpdateGenerateNum
from generate_data.ItemIntegrator.LabelMapper import LabelMapper
from generate_data.ItemIntegrator.IlluminationNormalization import IlluminationNormalization

operator_type_to_operator = {ItemBlender.type: ItemBlender, ItemsToImage.type: ItemsToImage,
                             ColorBackground.type: ColorBackground, RandomNoiseBackground.type: RandomNoiseBackground,
                             FileBackground.type: FileBackground, SeedItemPicker.type: SeedItemPicker,
                             UpdateGenerateNum.type: UpdateGenerateNum, LabelMapper.type: LabelMapper,
                             IlluminationNormalization.type: IlluminationNormalization}