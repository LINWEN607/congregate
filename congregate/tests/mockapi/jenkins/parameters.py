class ParametersApi():
    def get_parameters(self):
        return [
            {
                "name": "Boolean Parameter",
                "defaultValue": True
            },
            {
                "name": "Choice Parameter"
            },
            {
                "name": "Credentials Parameter",
                "defaultValue": "global_secret"
            },
            {
                "name": "/some/location/here"
            },
            {
                "name": "ML string param",
                "defaultValue": "line 1\nline 2\n\nline 4"
            },
            {
                "name": "password param",
                "defaultValue": "{AQAAABAAAAAQ/0s+qQwVGzQ4XYZBxxmmtQ3+i4SFM138cLG7U2X/598=}"
            },
            {
                "name": "string param",
                "defaultValue": "string"
            },
            {
                "name": "string param",
                "defaultValue": "string2"
            },
            {
                "name": "Git Parameter",
                "defaultValue": "origin/master"
            },
            {
                "name": "run parameter"
            }
        ]

    def get_single_parameter(self):
        return {
            "name": "Boolean Parameter",
            "defaultValue": True
        }

    def get_single_parameter_no_default_param(self):
        return {
            "name": "run parameter"
        }