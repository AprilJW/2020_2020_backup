from generate_data import operator_factory

class GenerateConfig:
    """
        generate config
        attribute:
            algo_names: transform algo order
            algo_to_params: algo_name: algo params
            generate_params: dict of generate params
            label_to_density_gennum: density of items in one image and uncovered items num in total date set
    """
    density_gennum_params = ['SeedNum', 'DensityMin', 'DensityMax', 'GenNum']
    attachment_params = ['num', 'prob']

    def __init__(self, data=None, generate_image_num=0):
        self.generate_image_num = generate_image_num
        self.label_to_items = {}  # item label : items
        self.label_to_attachment = {}  # attach label: attach items
        self.label_to_density_gennum = {}  # item label: param
        self.label_to_attachment_list = {}  # item label : {attach label : attach param}
        self.seed_path = ""
        self.attachment_path = ""
        self.stop_condition = ''

        if data is not None:
            self.__dict__.update(data)

    def update_label_to_density_gennum(self, label_to_items={}, label_to_density_gennum_from_config_json={}):
        label_to_density_gennum = {}
        for label, items in label_to_items.items():
            label_to_density_gennum[label] = {}
            for param in self.density_gennum_params:
                label_to_density_gennum[label][param] = label_to_density_gennum_from_config_json[label][param] if label_to_density_gennum_from_config_json else 0
            label_to_density_gennum[label]["SeedNum"] = len(items)
        return label_to_density_gennum

    def update_label_to_attachment_list(self, label_to_items={}, label_to_attachment={}, label_to_attachment_list={}):
        for item_label in label_to_items:
            if item_label not in label_to_attachment_list:
                label_to_attachment_list[item_label] = {}
        for label in label_to_attachment_list.keys():
            for attachment_label in label_to_attachment:
                if attachment_label not in label_to_attachment_list[label]:
                    label_to_attachment_list[label][attachment_label] = {}
                    for atachment_param in GenerateConfig.attachment_params:
                        label_to_attachment_list[label][attachment_label][atachment_param] = 0
                    label_to_attachment_list[label][attachment_label]["seedNum"] = 1
        return label_to_attachment_list

    def _get_all_operator_name(self):
        opt_dict = operator_factory.get_all_operator()
        operator_names = []
        operator_names.append(opt_name for opt_name in opt_dict.keys())
        return operator_names

    def _get_all_operator_param_dicts(self):
        """
            using processor Dict generate algo param dict
        :return:
        """
        opt_dict = operator_factory.get_all_operator()
        _opt_to_param_dict = {}
        for opt_name, opt in opt_dict.items():
            _operator_param = {}
            if len(opt.__subclasses__()) > 0:
                for sub_class in opt.__subclasses__():
                    _operator_param = sub_class().__dict__
                    _operator_param.update({'sub_type': sub_class.type})
                    _opt_to_param_dict[opt_name] = _operator_param
            else:
                _operator_param = opt().__dict__
                _opt_to_param_dict[opt_name] = _operator_param

        return _opt_to_param_dict
