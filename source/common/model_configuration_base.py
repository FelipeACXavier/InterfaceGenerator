from common.keys import KEY_MODEL_PATH
from tools import file_system

class ModelConfigurationBase:
    def __init__(self):
        self.data = None

    def parse(self, filename : str):
        if not self.data:
            raise Exception("No configuration data")

    def write(self, filename : str):
        raise Exception("Not implemented")

    def __str__(self):
        raise Exception("Not implemented")

    def __setitem__(self, key, value):
        raise Exception("Not implemented")

    def __getitem__(self, key):
        raise Exception("Not implemented")

    def has(self, key):
        raise Exception("Not implemented")