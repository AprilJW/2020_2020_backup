class ItemProcessor:

    def __init__(self, parent_generator=None, is_used=True, **kwargs):
        self.parent_generator = parent_generator
        self.is_used = is_used
        # not_display contains the parameters that will not be shown on UI.
        self.not_display = ["parent_generator", "not_display"]

    @classmethod
    def _check_input_is_satisfied(cls, input_keys, key_to_inputs):
        return all(input_key in key_to_inputs for input_key in input_keys)

    def process(self, key_to_inputs={}):
        pass
