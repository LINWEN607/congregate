class ParametersApi():
    def get_parameters(self):
        return [
            {
                "@name": "Checkbox_Param",
                "@value": "true",
                "type": {
                    "@rawValue": "checkbox uncheckedValue='false' display='prompt' checkedValue='true'"
                }
            },
            {
                "@name": "Masked_Param",
                "type": {
                    "@rawValue": "password display='normal'"
                }
            },
            {
                "@name": "Select_Param",
                "@value": "",
                "type": {
                    "@rawValue": "select data_2='Select 2' data_1='Select 1' data_4='Select 5' display='prompt' data_3='Select 3'"
                }
            },
            {
                "@name": "Unmasked_Param",
                "@value": "Unmasked Value"
            }
        ]

    def get_single_parameter(self):
        return {
            "@name": "Checkbox_Param",
            "@value": "true",
            "type": {
                "@rawValue": "checkbox uncheckedValue='false' display='prompt' checkedValue='true'"
            }
        }

    def get_single_parameter_no_default_param(self):
        return {
            "@name": "Masked_Param",
            "type": {
                "@rawValue": "password display='normal'"
            }
        }
