import os
import sys

from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from copy import copy
from datetime import datetime
from itertools import chain
from json import dumps as json_dumps
from tkinter import filedialog
from typing import Any, TypeAlias, TypeVar

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

# Common suffixes for movement classes.
MOVEMENT_SUFFIXES = ('Movement', 'Rider')

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

# Dictionary for converting numbers to words.
numbers = {
    0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four',
    5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine',
    10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen',
    14: 'fourteen', 15: 'fifteen', 16: 'sixteen', 17: 'seventeen',
    18: 'eighteen', 19: 'nineteen', 20: 'twenty', 30: 'thirty',
    40: 'forty', 50: 'fifty', 60: 'sixty', 70: 'seventy',
    80: 'eighty', 90: 'ninety',  # ... and so on
    # integers up to 99 should suffice for now
}

# Function to convert a number to words using the above dictionary.
def spell(number: int, limit: int = 100) -> str:
    if number > 99 or number < 0 or number >= limit:
        return str(number)
    if number in numbers:
        return numbers[number]
    if number > 19:
        tens = number // 10 * 10
        ones = number % 10
        if ones:
            return spell(tens) + '-' + spell(ones)
        return str(number)
    return str(number)


# Dictionary to get the ordinal suffix for a number.
ordinal_suffixes = defaultdict(lambda: 'th', {1: 'st', 2: 'nd', 3: 'rd'})


# Function to convert a number to an ordinal string (e.g. 1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', etc.).
def ordinal(number: int) -> str:
    if 10 <= number % 100 <= 20:
        return f"{number}th"
    return f"{number}{ordinal_suffixes[number % 10]}"


# Dictionary to get the ordinal form of a number.
ordinals = {
    1: 'first', 2: 'second', 3: 'third',
    5: 'fifth', 8: 'eighth', 9: 'ninth',
    12: 'twelfth', # others are regular
}


# Function to convert a number to an ordinal string using the above dictionary.
def spell_ordinal(number: int, limit: int = 100) -> str:
    if number > 99 or number < 0 or number >= limit:
        return ordinal(number)
    if number in ordinals:
        return ordinals[number]
    if number > 19:
        tens = number // 10 * 10
        ones = number % 10
        if ones:
            return spell(tens) + '-' + spell_ordinal(ones)
        return spell(tens).replace('ty', 'tie') + 'th'
    return spell(number) + 'th'


# Function to get the correct form of a word based on a number (e.g. '1 apple', '2 apples').
def pluralize(number: int | str, singular: str | None = None, plural: str | None = None) -> str:
    if isinstance(number, str):
        number, singular, plural = 2, number, singular
    if singular is None:
        return spell_ordinal(number)  # just in case
    if plural is None:
        if singular.endswith('y'):
            plural = singular[:-1] + 'ies'
        elif any(singular.endswith(suffix) for suffix in ('s', 'x', 'z', 'ch', 'sh', 'zh')):
            plural = singular + 'es'
        else:
            plural = singular + 's'
    return singular if number == 1 else plural


T = TypeVar('T')
TypeOr: TypeAlias = type[T] | T
Unpacked: TypeAlias = Sequence[T] | T
StringIndex: TypeAlias = Mapping[str, T]
IntIndex: TypeAlias = Sequence[T] | Mapping[int, T]
Index: TypeAlias = IntIndex[T] | StringIndex[T]
Key: TypeAlias = str | int
AnyJsonType = str | int | float | bool | None
AnyJson = dict | list | AnyJsonType


# Function to remove duplicate entries from a list while preserving order.
def deduplicate(l: list[T]) -> list[T]:
    return list(dict.fromkeys(l))


# Function to turn a sequence into its single element if it has exactly one element. If not, returns the Sequence as is.
def unpack(l: Sequence[T], bound: type = Sequence) -> Unpacked[T]:
    return l[0] if isinstance(l, bound) and not isinstance(l, str) and len(l) == 1 else l


# Function to turn any non-sequence object into a one-element sequence containing the object or return a Sequence as is.
def repack(l: Unpacked[T], bound: type = Sequence) -> Sequence[T]:
    return l if isinstance(l, bound) and not isinstance(l, str) else [l]


# Function to traverse any data object using sequences of keys or indices. Returns the values at the specified location.
def find(data: Index[T], *fields: Key) -> Collection[T] | None:
    if not fields:
        return data if isinstance(data, Collection) else (data,)
    if isinstance(data, Sequence) and isinstance(fields[0], str):
        return chain.from_iterable(find(x, *fields) for x in data)
    try:
        return find(data[fields[0]], *fields[1:])
    except (IndexError, KeyError, TypeError):
        return ()


# Simple template matching function. Matches an object or a group thereof with a template, and treats '*' as a wildcard.
def fits(template: str, data: Any) -> bool:
    if not template:
        return False
    if data is None:
        return False
    if template == '*':
        return True
    if not isinstance(data, str):
        if isinstance(data, Collection):
            return any(fits(template, s) for s in data)
        data = str(data)
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
    return False


# Function to check if a string contains another string as a prefix, a suffix, or a substring, optionally ignoring case.
def find_string(string: Any, part: Any, side: int = 0, case: bool = False) -> bool:
    if not isinstance(string, str) or not isinstance(part, str):
        return False
    if not case:
        string, part = string.lower(), part.lower()
    return part in string if not side else (string.startswith(part) if side < 0 else string.endswith(part))


# Function to generate a file name based on a name, extension and timestamp (if not provided, the current time is used).
def get_file_name(name: str, ext: str, ts: datetime | None = None, ts_format: str = "%Y-%m-%d_%H-%M-%S") -> str:
    name_args = [name, (ts or datetime.now()).strftime(ts_format)]
    full_name = '_'.join(s for s in name_args if s).translate(invalid_chars_trans_table)
    return f"{full_name}.{ext}"


# Function to generate a default path for saving or loading files.
def get_file_path(name: str, ext: str, path: str = '') -> str:
    return normalize(os.path.join(base_dir, path, get_file_name(name, ext)))


# Function to select a file to open. Returns the path of the selected file.
def load_menu(path: str = base_dir, file: str = None) -> str:
    return filedialog.askopenfilename(
        initialdir=path,
        initialfile=file,
        filetypes=[("JSON file", "*.json")],
    )


# Function to select a file to save. Returns the path of the selected file.
def save_menu(path: str = base_dir, file: str = None) -> str:
    return filedialog.asksaveasfilename(
        initialdir=path,
        initialfile=file,
        filetypes=[("JSON file", "*.json")],
        defaultextension='.json',
    )


# Function to convert a path to an absolute path and change all path separators to the one provided (os.sep by default).
def normalize(path: str, sep: str = os.sep) -> str:
    return os.path.abspath(path).translate(str.maketrans('\\/', sep * 2))


# Function to find the correct texture path based on the provided paths.
def get_texture_path(*paths: str) -> str:
    for path in paths:
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


# Function to check if a given object is a layered collection with a specified level of depth. Used for JSON formatting.
def is_layered(obj: AnyJson, depth: int = 0) -> bool:
    if not isinstance(obj, (dict, list)):
        return False
    if not depth:
        return True
    if isinstance(obj, dict):
        obj = obj.values()
    for i in range(depth):
        fi = chain.from_iterable
        obj = fi(sub.values() if isinstance(sub, dict) else sub if isinstance(sub, list) else () for sub in obj)
    for _ in obj:
        return True
    return False


# Alternative JSON dump function that allows for more control over the output format.
def dumps(data: AnyJson, **kwargs: Any) -> str:
    compression = kwargs.pop('compression', 0)
    if not compression:
        return json_dumps(data, **kwargs)
    result = ''
    stack = [copy(data)]
    info_stack = [{'depth': 0, 'pad': 0, 'compress': not is_layered(stack[-1], compression)}]
    indent = kwargs.pop('indent', None)
    nl = '' if indent is None else '\n'
    indent = indent or 0
    item_sep, key_sep = kwargs.pop('separators', ('', ''))
    item_sep, key_sep = item_sep or ', ', key_sep or ': '
    strip = kwargs.pop('strip', True)
    sep = ''
    while True:
        if not stack:
            return result
        item = stack[-1]
        info = info_stack[-1]
        start = ''
        if info['depth'] < len(stack):
            if isinstance(item, dict):
                start = '{'
            elif isinstance(item, list):
                start = '['
            if start:
                compress = not is_layered(item, compression)
                info_stack.append(
                    {'depth': info['depth'] + 1, 'pad': info['pad'] + (not info['compress']), 'compress': compress}
                )
                if not info_stack[-1]['compress'] and sep:
                    if strip:
                        result = result.rstrip()
                    result += f"{nl}{'':{info['pad'] * indent}}"
                sep = ''
                result += f"{start}"
        end = ''
        info = info_stack[-1]
        if isinstance(item, dict):
            if not item:
                sep = item_sep
                end = "}"
            else:
                result += sep
                k = next(iter(item))
                v = stack[-1].pop(k)
                if not info['compress']:
                    if strip:
                        result = result.rstrip()
                    result += f"{nl}{'':{info['pad'] * indent}}"
                if not isinstance(k, str):
                    k = json_dumps(k, **kwargs)
                result += f'"{k}"{key_sep}'
                stack.append(copy(v))
        elif isinstance(item, list):
            if not item:
                sep = item_sep
                end = "]"
            else:
                if start and not info['compress']:
                    if strip:
                        result = result.rstrip()
                    result += f"{nl}{'':{info['pad'] * indent}}"
                result += sep
                stack.append(copy(stack[-1].pop(0)))
        else:
            stack.pop()
            result += json_dumps(item, **kwargs)
            sep = item_sep
        if end:
            stack.pop()
            compress = info_stack.pop()['compress']
            info = info_stack[-1]
            if not start and not compress:
                if strip:
                    result = result.rstrip()
                result += f"{nl}{'':{info['pad'] * indent}}"
            result += end


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


# Metaclass used for overriding the __str__ and/or __repr__ methods of a class.
class FormatOverride(type):
    def __new__(mcs, name, bases, namespace, *, str_method=None, repr_method=None):
        cls = super().__new__(mcs, name, bases, namespace)
        if str_method is not None:
            mcs.__str__ = str_method
        if repr_method is not None:
            mcs.__repr__ = repr_method
        return cls


# Context manager for temporarily disabling print statements. Anything in a "with no_print()" block will not be printed.
class no_print:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
