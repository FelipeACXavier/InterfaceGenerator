import os

from pathlib import Path

from tools import file_system, matlab

from common.keys import *
from common.result import *
from common.model_configuration_base import ModelConfigurationBase

from interface.matlab_generator import ServerGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGeneratorMatlab2024a(ServerGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)
        self.output_file = output_file + "_server.m"

        file_system.copy_archive(f'{engine_folder}/../../common/languages/java/Helpers.java', f'{os.path.dirname(output_file)}/dtig/Helpers.java')

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        self.engine_template_file = f'{engine_folder}/matlab_callbacks.m'

        return super().generate(config)

    def parse_dtig_language(self):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: variable_type
        dtig_parser.to_proto_message = lambda variable_type: matlab.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'\"{variable_type}\"'

        return super().parse_dtig_language(dtig_parser)