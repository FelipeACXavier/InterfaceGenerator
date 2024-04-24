import os
import re

from pathlib import Path

from common.keys import *
from common.result import *
from common.logging import *

from tools import cpp
from tools.file_system import create_dir
from common.model_configuration_base import ModelConfigurationBase

from interface.cpp_generator import HppGenerator, CppGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)
template_folder = engine_folder + "/templates"

PARAMETER_HANDLER = "mAttributeHandler"
INPUT_HANDLER = "mInputHandler"
OUTPUT_HANDLER = "mOutputHandler"

class ClientGeneratorRTI1516():
    def __init__(self, output_file):
        self.output_file = output_file

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        # self.generate_model_config()

        # Output file names
        federate_header = self.output_file + "_federate.h"
        federate_source = self.output_file + "_federate.cpp"

        ambassador_header = self.output_file + "_ambassador.h"
        ambassador_source = self.output_file + "_ambassador.cpp"

        # Federate generators
        federate_hpp = HppGeneratorRTI1516(federate_header)
        federate_hpp.common_template_file = template_folder + "/federate_template.h"

        federate_cpp = CppGeneratorRTI1516(federate_source, Path(federate_header).name)
        federate_cpp.common_template_file = template_folder + "/federate_template.cpp"

        # Ambassador generators
        ambassador_hpp = HppGeneratorRTI1516(ambassador_header)
        ambassador_hpp.common_template_file = template_folder + "/ambassador_template.h"

        ambassador_cpp = CppGeneratorRTI1516(ambassador_source, Path(ambassador_header).name)
        ambassador_cpp.common_template_file = template_folder + "/ambassador_template.cpp"

        # =======================================================================================
        # Begin generation
        # First the ambassador
        generated = ambassador_hpp.generate(config)
        if not generated:
            return generated

        generated = ambassador_cpp.generate(config)
        if not generated:
            return generated

        # Then the federate
        # Make the ambassador configuration available to the federate
        ambassador_name = ambassador_hpp.callbacks[KEY_CLASS_NAME]
        federate_hpp.new_callback("AMBASSADOR", ambassador_name)
        federate_hpp.new_callback("AMBASSADOR_HEADER", {KEY_NAME: None, KEY_BODY: Path(ambassador_header).name, KEY_SELF: False})
        federate_cpp.new_callback("AMBASSADOR", ambassador_name)
        federate_cpp.new_callback("AMBASSADOR_HEADER", {KEY_NAME: None, KEY_BODY: Path(ambassador_header).name, KEY_SELF: False})

        generated = federate_hpp.generate(config)
        if not generated:
            return generated

        generated = federate_cpp.generate(config)
        if not generated:
            return generated

        return VoidResult()

class HppGeneratorRTI1516(HppGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: variable_type
        dtig_parser.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)

class CppGeneratorRTI1516(CppGenerator):
    def __init__(self, output_file, header_name = None):
        super().__init__(output_file, header_name)

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: cpp.to_type(variable_type)
        dtig_parser.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)