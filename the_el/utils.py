import os

from django.conf import settings


def get_key(key_file_name):
    """
    Loads the text file associated with key_file_name and returns the key found there.
    """
    with open(os.path.join(settings.DATA_DIR, key_file_name)) as keyfile:
        return keyfile.readline().strip()
