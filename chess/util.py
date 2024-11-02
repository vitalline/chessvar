import os
import sys

from datetime import datetime
from tkinter import filedialog
from typing import Any

# Lambda function to remove duplicates from a list while preserving order.
deduplicate = lambda lst: list(dict.fromkeys(lst))

# Lambda function to return the sign of a number. Returns +1 for positive numbers, -1 for negative numbers, and 0 for 0.
sign = lambda x: (x > 0) - (x < 0)

# Dummy value used to indicate reverting to default value in functions where None indicates retaining the current value.
Default = object()

# Dummy value used to indicate a value that has not been set and should be set to a non-None value (e.g. for promotion).
Unset = frozenset()

# String used to represent Unset values in JSON files.
UNSET_STRING = '*'

# Prefix for custom piece and/or movement classes.
CUSTOM_PREFIX = '_custom_'

# Path to the directory where the game is running.
base_dir = os.path.abspath(os.curdir)

# Path to the game's configuration file.
config_path = os.path.join(base_dir, 'config.ini')

# Placeholder texture path for non-existent files.
default_texture = "assets/util/missingno.png"

# Characters that are invalid in file names.
invalid_chars = ':<>|"?*'

# Translation table to replace invalid characters with underscores.
invalid_chars_trans_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))


# Simple template matching function. Matches a string (or a group thereof) with a template containing '*' as a wildcard.
def fits(template: str, data: Any) -> bool:
    if not template:
        return False
    if data is None:
        return False
    if not isinstance(data, str):
        return any(fits(template, s) for s in data)
    if template == '*':
        return True
    if template == data:
        return True
    if '*' not in template:
        return False
    template_start = template[0] == '*'
    template_end = template[-1] == '*'
    template = template.strip('*')
    template_middle = '*' in template
    if template_middle:
        keys = template.split('*')
        if not template_start and not data.startswith(keys[0]):
            return False
        if not template_end and not data.endswith(keys[-1]):
            return False
        indexes = [data.find(key) for key in keys]
        return all(index >= 0 for index in indexes) and indexes == sorted(indexes)
    if template_start and template_end:
        return template in data
    if template_start:
        return data.endswith(template)
    if template_end:
        return data.startswith(template)


# Function to generate a file name based on a name, extension and timestamp (if not provided, the current time is used).
def get_filename(
    name: str, ext: str, in_dir: str = base_dir, ts: datetime | None = None, ts_format: str = "%Y-%m-%d_%H-%M-%S"
) -> str:
    name_args = [name, (ts or datetime.now()).strftime(ts_format)]
    full_name = '_'.join(s for s in name_args if s).translate(invalid_chars_trans_table)
    return os.path.join(in_dir, f"{full_name}.{ext}")


# Function to check if a string is a prefix of another string, ignoring case.
def is_prefix_of(string: Any, prefix: Any) -> bool:
    return isinstance(string, str) and isinstance(prefix, str) and string.lower().startswith(prefix.lower())


# Function to check if a string is a prefix of any string in a list, ignoring case.
def is_prefix_in(strings: list[Any], prefix: Any) -> bool:
    return any(is_prefix_of(string, prefix) for string in strings)


# Function to check if a string has a prefix from a list of prefixes, ignoring case.
def has_prefix_in(string: Any, prefixes: list[Any]) -> bool:
    return any(is_prefix_of(string, prefix) for prefix in prefixes)


# Function to select a file to open. Returns the path of the selected file.
def select_save_data() -> str:
    return filedialog.askopenfilename(
        initialdir=base_dir,
        filetypes=[("JSON save file", "*.json")],
    )


# Function to select a file to save. Returns the path of the selected file.
def select_save_name() -> str:
    return filedialog.asksaveasfilename(
        initialdir=base_dir,
        initialfile=get_filename('save', 'json', in_dir=''),
        filetypes=[("JSON save file", "*.json")],
        defaultextension='.json',
    )


# Function to find the correct texture path based on the provided path.
def get_texture_path(path: str) -> str:
    if os.path.isabs(path):
        if os.path.isfile(path):
            return path
    else:
        base_path = os.path.join(base_dir, path)
        if os.path.isfile(base_path):
            return base_path
        curr_path = os.path.join(os.getcwd(), path)
        if os.path.isfile(curr_path):
            return curr_path
    return default_texture


# Function to find the first method with a given name in the MRO of a given object. Used for dynamic super()-like calls.
def dynamic_super(obj):
    def get(method, cls=None):
        if cls is None:
            cls = type(obj)
        elif not isinstance(obj, cls):
            raise TypeError(f"Object {obj} is not an instance of {cls}")
        for base in cls.__mro__:
            if method in base.__dict__:
                return lambda *args, **kwargs: base.__dict__[method](obj, *args, **kwargs)
        raise AttributeError(f"Method '{method}' not found in MRO for {cls}")

    class MROCache:
        def __init__(self):
            self.cache = {}

        class MethodWrapper:
            def __init__(self, cls=None):
                self.cls = cls

            def __getattr__(self, method):
                setattr(self, method, get(method, self.cls))
                return getattr(self, method)

            def __getitem__(self, item):
                return self.__getattr__(item)

        def __getitem__(self, item):
            if item not in self.cache:
                self.cache[item] = self.MethodWrapper(item)
            return self.cache[item]

    return MROCache()


# Context manager for temporarily disabling print statements. Anything in a "with no_print()" block will not be printed.
class no_print:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
