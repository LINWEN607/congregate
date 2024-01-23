from flask import Blueprint, jsonify
from congregate.helpers.configuration_validator import ConfigurationValidator

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods=['GET'])
def get_config():
    c = ConfigurationValidator()
    scrubbed_config = strip_tokens(c)
    return jsonify(scrubbed_config), 200

def strip_tokens(config):
    scrubbed_config = {}
    for section, settings in config.as_dict().items():
        scrubbed_config[section] = {}
        for setting, value in settings.items():
            if 'token' not in setting:
                scrubbed_config[section][setting] = value
    return scrubbed_config
