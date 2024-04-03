import os

from common.result import *
from common.model_configuration_base import ModelConfigurationBase

from interface.python_generator import ServerGenerator, ClientGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGeneratorFMI2(ServerGenerator):
  def __init__(self, output_file):
    super().__init__(output_file)
    self.output_file += "_server.py"

  def generate(self, config : ModelConfigurationBase) -> VoidResult:
    self.config = config
    self.engine_template_file = engine_folder + "/server_callbacks.py"
    return super().generate(config)

# =============================================================
# Client generator

class ClientGeneratorFMI2(ClientGenerator):
  def __init__(self, output_file):
    super().__init__(output_file)
    self.output_file += "_client.py"

  def generate(self, config : ModelConfigurationBase) -> VoidResult:
    return VoidResult()