import os

from common.result import *
from common.model_configuration_base import ModelConfigurationBase

from interface.matlab_generator import ServerGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGeneratorSimulink():
  def __init__(self, output_file):
    self.output_file = output_file + "_server.m"

  def generate(self, config : ModelConfigurationBase) -> VoidResult:
    matlab_generator = ServerGenerator(self.output_file)
    return matlab_generator.generate(config)
