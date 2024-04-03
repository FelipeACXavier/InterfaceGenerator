import json

from common.model_configuration_base import ModelConfigurationBase

class JsonConfiguration(ModelConfigurationBase):
  def __init__(self):
    super().__init__()

  def parse(self, filename : str):
    with open(filename, "r") as file:
      self.data = json.load(file)

  def __str__(self):
    return json.dumps(self.data, indent=2)

  def __getitem__(self, key):
    return self.data[key]

  def has(self, key):
    return key in self.data