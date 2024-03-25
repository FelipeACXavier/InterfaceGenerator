class ModelConfigurationBase:
  def __init__(self):
    self.data = None

  def parse(self, filename : str):
    print(f'Loading config from file: {filename}')
    raise Exception("Not implemented")

  def write(self, filename : str):
    raise Exception("Not implemented")

  def __str__(self):
    raise Exception("Not implemented")

  def __getitem__(self, key):
    raise Exception("Not implemented")

  def has(self, key):
    raise Exception("Not implemented")