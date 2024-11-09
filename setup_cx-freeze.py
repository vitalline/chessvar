from os import walk
from os.path import join
from pathlib import PurePath
from typing import Iterable

from cx_Freeze import setup, Executable


def gen_data_files(include: Iterable[str], exclude: Iterable[str] = ()):
    data_files = []
    for directory in include:
        for root, dirs, files in walk(directory):
            for file in files:
                path = PurePath(join(root, file))
                for excluded in exclude:
                    if path.is_relative_to(excluded):
                        path = None
                        break
                if path is not None:
                    data_files += [(path, path)]
    return data_files


setup(
    name='chess',
    version='0.3.0',
    options={'build_exe': {
        'build_exe': join('dist', 'chess'),
        'include_files': gen_data_files(['assets']) + [
            (s,) * 2 for s in (
                'cwda_2024.txt',
                'config.txt',
                'readme.txt',
                'source.txt',
            )
        ]
    }},
    executables=[
        Executable('main.py', target_name='chessvar.exe'),
        Executable('main.py', target_name='chessvarw.exe', base='Win32GUI'),
    ]
)
