import importlib
import os
import sys


def test_import():
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
    )
    gitlab_users = importlib.import_module("gitlab_users")
    assert hasattr(gitlab_users, "__version__")
