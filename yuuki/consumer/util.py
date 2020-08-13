import json
import os
from importlib import resources


YUUKI_CONFIG_TEMPLATE_FILE_NAME = 'template_yuuki_config.json'
YUUKI_CONFIG_FILE_NAME = 'yuuki_config.json'

def parse_custom_config(config_path):
    config = None
    with open(config_path) as my_config:
        try:
            config = json.loads(my_config.read())
        except Exception as e:
            print('Problem with config file ({}):'.format(config_path))
            print(e)
    return config


def write_out_template_config():
    my_config = resources.open_text('yuuki.consumer', YUUKI_CONFIG_TEMPLATE_FILE_NAME)
    with open(YUUKI_CONFIG_FILE_NAME,'x') as new_file:
        new_file.write(my_config.read())
    result_path = os.getcwd()
    result_path = os.path.join(result_path, YUUKI_CONFIG_FILE_NAME)
    if os.path.exists(result_path):
        print('Wrote default config at:')
        print(result_path)
    else:
        print('Unexpected problem')