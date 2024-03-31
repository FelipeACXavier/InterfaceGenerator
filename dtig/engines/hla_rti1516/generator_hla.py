import os

from pathlib import Path

from dtig.common.keys import *
from dtig.common.result import *
from dtig.common.model_configuration_base import ModelConfigurationBase

from dtig.interface.cpp_generator import HppGenerator, CppGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ClientGeneratorRTI1516():
  def __init__(self):
    pass

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    self.config = config
    # Ambassador generator
    federate_header = output_file + "_federate.h"
    ambassador_header = output_file + "_ambassador.h"

    federate_hpp = HppGenerator()
    federate_hpp.common_template_file = engine_folder + "/templates/federate_template.h"

    federate_cpp = CppGenerator(Path(federate_header).name)
    federate_cpp.common_template_file = engine_folder + "/templates/federate_template.cpp"

    ambassador_hpp = HppGenerator()
    ambassador_hpp.common_template_file = engine_folder + "/templates/ambassador_template.h"

    ambassador_cpp = CppGenerator(Path(ambassador_header).name)
    ambassador_cpp.common_template_file = engine_folder + "/templates/ambassador_template.cpp"

    # =======================================================================================
    # Begin generation
    # First the ambassador
    generated = ambassador_hpp.generate(ambassador_header, config)
    if not generated:
        return generated

    generated = ambassador_cpp.generate(output_file + "_ambassador.cpp", config)
    if not generated:
        return generated

    # Then the federate
    # Make the ambassador configuration available to the federate
    ambassador_name = ambassador_hpp.callbacks[KEY_CLASS_NAME]
    federate_hpp.new_callback("ambassador", ambassador_name)
    federate_hpp.new_callback("ambassador_header", {KEY_NAME: Path(ambassador_header).name, KEY_BODY: "", KEY_SELF: False})
    federate_cpp.new_callback("ambassador", ambassador_name)
    federate_cpp.new_callback("ambassador_header", {KEY_NAME: Path(ambassador_header).name, KEY_BODY: "", KEY_SELF: False})

    generated = federate_hpp.generate(federate_header, config)
    if not generated:
        return generated

    generated = federate_cpp.generate(output_file + "_federate.cpp", config)
    if not generated:
        return generated

    return VoidResult()
