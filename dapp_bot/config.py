import os
import configparser

def get_root_path(project_dir='dapp_bot'):
    current_dir = __file__
    while True:
        head_dir, tail_dir = os.path.split(current_dir)
        if head_dir and tail_dir != project_dir:
            current_dir = head_dir
        else:
            return current_dir

config = configparser.ConfigParser()
config_path = os.path.join(get_root_path(), 'config.ini')
config.read(config_path)

db_params = dict(config['db'])

token = config['bot']['token']

bonus_addr = config['bonus_tron_account']['address']
bonus_pkey = config['bonus_tron_account']['private_key']

