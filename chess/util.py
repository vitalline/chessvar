import os
import sys


# Dummy value used to indicate reverting to default value in functions where None indicates retaining the current value.
Default = object()

# Dummy value used to indicate a value that has not been set and should be set to a non-None value (e.g. for promotion).
Unset = frozenset()

# Path to the directory where the game is running.
base_dir = os.path.abspath(os.curdir)

# Placeholder texture path for non-existent files.
default_texture = "assets/util/missingno.png"


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
