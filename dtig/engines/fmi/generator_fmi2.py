import os

from dtig.tools import python

from dtig.common.logging import *
from dtig.common.result import *
from dtig.common.model_configuration_base import ModelConfigurationBase

from dtig.interface.python_generator import ServerGenerator, ClientGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGeneratorFMI2(ServerGenerator):
  def __init__(self):
    super().__init__()

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    self.config = config
    self.engine_template_file = engine_folder + "/server_callbacks.py"
    return super().generate(output_file + "_server.py", config)

# =============================================================
# Client generator

class ClientGeneratorFMI2(ClientGenerator):
  def __init__(self):
    super().__init__()

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    return VoidResult()