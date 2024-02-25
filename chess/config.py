from configparser import ConfigParser
from os.path import isfile
from typing import Any


DEFAULT_CONFIG = {
    'Chess': {
        'white_id': 0,
        'black_id': 0,
        'edit_id': '',
        'use_set_seed': False,
        'set_seed': 0,
        'use_roll_seed': False,
        'update_roll_seed': True,
        'roll_seed': 0,
        'block_ids': '',
    },
}


class Config(dict):
    def __init__(self, path: str):
        super().__init__()
        self.base_config = None
        self.load(path)

    def load(self, path: str) -> None:
        self.clear()
        self.base_config = ConfigParser()
        self.base_config.read_dict(DEFAULT_CONFIG)
        if isfile(path):
            self.base_config.read(path)
        for section in self.base_config:
            for item in self.base_config[section]:
                self[item] = self.base_config[section][item]
                if type(DEFAULT_CONFIG.get(section, {}).get(item, {})) is bool:
                    self[item] = self.base_config.getboolean(section, item)
                if type(DEFAULT_CONFIG.get(section, {}).get(item, {})) is int:
                    self[item] = self.base_config.getint(section, item)
                if item.startswith('block_'):
                    self[item] = [
                        int(s) for i in self.base_config[section][item].split(',') if (s := i.strip()).isdigit()
                    ]
                if item == 'edit_id':
                    if self.base_config[section][item].strip() == '':
                        self[item] = None
                    else:
                        self[item] = self.base_config.getint(section, item)

    def save(self, path) -> None:
        for section in self.base_config:
            for item in self.base_config[section]:
                self.base_config[section][item] = str(self[item])
                if item.startswith('block_'):
                    self.base_config[section][item] = ', '.join(str(s) for s in self[item])
                if item == 'edit_id' and self[item] is None:
                    self.base_config[section][item] = ''
        with open(path, 'w') as file:
            self.base_config.write(file)

    def __getitem__(self, key: str) -> Any:
        return self.get(key.lower())
