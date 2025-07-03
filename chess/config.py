from __future__ import annotations

from configparser import ConfigParser
from os.path import isfile
from typing import Any

DEFAULT_CONFIG = {
    "INIT": {
        'asset_path': 'assets',
        'color_id': 0,
        'white_id': 0,
        'black_id': 0,
        'edit_id': '',
        'edit_mode': False,
        'flip_board': False,
        'alter_pieces': 0,
        'alter_swap': False,
        'hide_pieces': 0,
        'hide_moves': '',
        'use_drops': False,
    },
    "SEED": {
        'block_ids': '',
        'block_ids_chaos': '',
        'chaos_mode': 0,
        'chaos_seed': '',
        'set_seed': '',
        'roll_seed': '',
        'update_roll_seed': True,
        'max_seed': 2 ** 32 - 1,
    },
    "SKIP": {
        'fast_moves': False,
        'fast_chain': True,
        'fast_drops': True,
        'fast_promotion': True,
        'fast_sequences': True,
        'fast_turn_pass': True,
    },
    "LOGS": {
        'log_path': 'logs',
        'log_pass': '',
        'log_info': True,
        'log_prefix': 1,
        'status_prefix': 1,
        'status_string': True,
        'timestamp': '',
        'timestamp_format': '%Y-%m-%d %H:%M:%S',
        'verbose': True,
    },
    "SAVE": {
        'save_path': 'save',
        'load_path': 'save',
        'load_save': '',
        'indent': '',
        'compression': 0,
        'update_mode': 0,
        'size_limit': '1M',
        'trim_save': False,
        'recursive_aliases': True,
    },
    "AUTO": {
        'autosave_path': 'auto',
        'autosave_act': 0,
        'autosave_ply': 0,
        'autosave_time': 0,
        'trim_autosave': False,
    },
    "SYNC": {
        'sync_data': False,
        'sync_host': 'localhost',
        'sync_port': 58084,
        'sync_time': 0,
    },
}


class Config(dict):
    def __init__(self, path: str = ''):
        super().__init__()
        self.base_config = None
        self.load(path)

    def load(self, path: str) -> None:
        self.clear()
        self.base_config = ConfigParser(interpolation=None)
        self.base_config.read_dict(DEFAULT_CONFIG)
        if isfile(path):
            self.base_config.read(path)
        for section in self.base_config:
            for item in self.base_config[section]:
                self[item] = self.base_config[section][item]
                try:
                    if type(DEFAULT_CONFIG.get(section, {}).get(item, {})) is bool:
                        self[item] = self.base_config.getboolean(section, item)
                    if type(DEFAULT_CONFIG.get(section, {}).get(item, {})) is int:
                        self[item] = self.base_config.getint(section, item)
                except ValueError:
                    self[item] = DEFAULT_CONFIG[section][item]
                if item in {'hide_moves', 'log_pass', 'status_string', 'timestamp', 'verbose'}:
                    try:
                        self[item] = self.base_config.getboolean(section, item)
                    except ValueError:
                        self[item] = None
                if item.startswith('block_'):
                    self[item] = [
                        int(s) for i in self.base_config[section][item].split(',') if (s := i.strip()).isdigit()
                    ]
                if item.startswith('size_'):
                    self[item] = 0
                    data = self.base_config[section][item].strip().upper()
                    if data[-1:] == 'B':
                        data = data[:-1]
                    exponent = {'K': 10, 'M': 20, 'G': 30, 'T': 40}.get(data[-1:], 0)
                    data = data[:-1] if exponent else data
                    if data.isdigit():
                        self[item] = int(data) << exponent
                if (
                    item == 'indent' or item.endswith('_id')
                    or (item.endswith('_seed') and not item.startswith('update_'))
                ):
                    if self.base_config[section][item].strip() == '':
                        self[item] = None
                    elif self.base_config[section][item].isdigit():
                        self[item] = self.base_config.getint(section, item)
                    else:
                        self[item] = self.base_config[section][item]

    def save(self, path: str) -> None:
        for section in self.base_config:
            for item in self.base_config[section]:
                if self[item] is None:
                    self.base_config[section][item] = ''
                elif item.startswith('block_'):
                    self.base_config[section][item] = ', '.join(str(s) for s in self[item])
                elif item.startswith('size_'):
                    value = self[item]
                    for exponent in ['', 'K', 'M', 'G', 'T']:
                        if value & 1023 == 0:
                            value >>= 10
                        else:
                            break
                    self.base_config[section][item] = f'{value}{exponent}'
                else:
                    self.base_config[section][item] = str(self[item])
        with open(path, mode='w', encoding='utf-8') as file:
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
