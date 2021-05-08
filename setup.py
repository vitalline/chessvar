from os import walk
from os.path import join
from distutils.core import setup
import py2exe


def gen_data_files(source_dirs):
    data_files = []
    for source_dir in source_dirs:
        for path, dirs, files in walk(source_dir):
            data_files.append((path, [join(path, file) for file in files]))
    return data_files


setup(
    name='chess',
    version='0.0.1',
    windows=['main.py'],
    packages=['chess'],
    data_files=gen_data_files([join('assets', 'pieces'), join('assets', 'util')]),
    url='',
    license='',
    author='vale.a',
    author_email='',
    description='',
)
