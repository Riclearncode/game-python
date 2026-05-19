import os
import sys


APP_NAME = "PixelZombieSiege"


def get_base_path():
    """Return the directory that contains bundled read-only game resources."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path=""):
    return os.path.join(get_base_path(), relative_path)


def user_data_dir():
    if getattr(sys, "frozen", False):
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(root, APP_NAME)
    else:
        path = os.path.join(get_base_path(), "save")
    os.makedirs(path, exist_ok=True)
    return path


def user_data_path(filename):
    return os.path.join(user_data_dir(), filename)
