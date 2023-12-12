from os import walk
from os.path import join
from cx_Freeze import setup, Executable


def gen_data_files(source_dirs):
    data_files = []
    for source_dir in source_dirs:
        for path, dirs, files in walk(source_dir):
            data_files += [(join(path, file), join(path, file)) for file in files]
    return data_files


setup(
    name='chess',
    version='0.0.2',
    options={'build_exe': {
        'build_exe': join('build', 'Chess'),
        'include_files': gen_data_files(['assets'])
    }},
    executables=[Executable('main.py', target_name='Chess.exe', base='Win32GUI')]
)
