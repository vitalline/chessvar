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


# Context manager for temporarily disabling print statements. Anything in a "with no_print()" block will not be printed.
class no_print:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
