from abc import ABC
from abc import abstractmethod
from dtig.common.result import VoidResult
from dtig.common.model_configuration_base import ModelConfigurationBase

class GeneratorBase(ABC):
  # Must be called from any children so members are initialized
  def __init__(self):
    self.output_file = None
    self.config = None

  @abstractmethod
  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    raise Exception("Not implemented")

  # @abstractmethod
  # def generate_constructor(self) -> VoidResult:
  #   raise Exception("Not implemented")