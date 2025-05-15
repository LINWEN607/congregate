from distutils.util import strtobool
from flask import Blueprint, jsonify
from congregate.helpers.configuration_validator import ConfigurationValidator

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods=['GET'])
def get_config():
    c = ConfigurationValidator()
    scrubbed_config = strip_tokens(c)
    return jsonify(scrubbed_config), 200

def strip_tokens(config):
    scrubbed_config = {
        'APP': {
            'flower_url': config.flower_url,
            'grafana_url': config.grafana_url
        }
    }
    for section, settings in config.as_dict().items():
        if scrubbed_config.get(section) is None:
            scrubbed_config[section] = {}
        for setting, value in settings.items():
            if 'token' not in setting:
                if value.lower() in ['true', 'false']:
                    scrubbed_config[section][setting] = strtobool(value)
                else:
                    scrubbed_config[section][setting] = value
    return scrubbed_config
