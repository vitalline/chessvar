from __future__ import annotations

from configparser import ConfigParser
from os.path import isfile
from typing import Any


DEFAULT_CONFIG = {
    'Chess': {
        'color_id': 0,
        'white_id': 0,
        'black_id': 0,
        'edit_id': '',
        'hide_pieces': 0,
        'hide_moves': '',
        'use_check': True,
        'royal_mode': 0,
        'chaos_mode': 0,
        'chaos_seed': '',
        'set_seed': '',
        'roll_seed': '',
        'update_roll_seed': True,
        'block_ids': '',
        'block_ids_chaos': '',
        'save_indent': '',
        'save_update_mode': 0,
        'autosave_act': 0,
        'autosave_ply': 0,
        'autosave_time': 0,
    },
}


class Config(dict):
    def __init__(self, path: str = ''):
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
                if (
                    item == 'save_indent'
                    or item.endswith('_id')
                    or (item.endswith('_seed') and not item.startswith('update_'))
                ):
                    if self.base_config[section][item].strip() == '':
                        self[item] = None
                    else:
                        self[item] = self.base_config.getint(section, item)
                if item == 'hide_moves':
                    if self.base_config[section][item].strip() == '':
                        self[item] = None
                    else:
                        self[item] = self.base_config.getboolean(section, item)

    def save(self, path: str) -> None:
        for section in self.base_config:
            for item in self.base_config[section]:
                self.base_config[section][item] = str(self[item])
                if item.startswith('block_'):
                    self.base_config[section][item] = ', '.join(str(s) for s in self[item])
                if (
                    item == 'save_indent'
                    or item.endswith('_id')
                    or (item.endswith('_seed') and not item.startswith('update_'))
                ):
                    if self[item] is None:
                        self.base_config[section][item] = ''
                if item == 'hide_moves':
                    if self[item] is None:
                        self.base_config[section][item] = ''
        with open(path, 'w') as file:
            self.base_config.write(file)

    def __copy__(self) -> Config:
        copy = Config()
        for section in self.base_config:
            for item in self.base_config[section]:
                copy.base_config[section][item] = self.base_config[section][item]
        for item in self:
            copy[item] = self[item]
        return copy

    def __deepcopy__(self, memo) -> Config:
        copy = Config()
        for section in self.base_config:
            for item in self.base_config[section]:
                copy.base_config[section][item] = self.base_config[section][item].__deepcopy__(memo)
        for item in self:
            copy[item] = self[item].__deepcopy__(memo)
        return copy

    def __getitem__(self, key: str) -> Any:
        return super().get(key.lower())

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key.lower(), value)
