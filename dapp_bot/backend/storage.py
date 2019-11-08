import utils

from exceptions import *


class PKeyStorage:
    def __init__(self):
        self.storage = {}

    def generate_random_path(self, limit=10):
        while True:
            path = utils.create_sequence(limit)
            if not self.is_existing_path(path):
                return path

    def reg_path(self, path, pkey):
        self.storage[path] = pkey

    def get_pkey_by_path(self, path):
        try:
            return self.storage[path]
        except KeyError:
            raise PKeyNotFound

    def remove_pkey_path(self, path):
        del self.storage[path]

    def is_existing_path(self, path):
        return path in self.storage

    def create_link(self, pkey):
        path = self.generate_random_path()
        self.reg_path(path, pkey)
        return 'http://127.0.0.1:8080/pkey/' + path

pkey_storage = PKeyStorage()

