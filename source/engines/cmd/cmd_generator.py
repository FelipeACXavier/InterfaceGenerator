import os

from tools import python
from common.keys import *
from common.result import *
from common.model_configuration_base import ModelConfigurationBase

from interface.python_generator import ClientGenerator, ServerGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)
template_folder = engine_folder + "/templates"

class ClientGeneratorCMD(ClientGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)
        self.output_file += ".py"

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        self.engine_template_file = f'{template_folder}/client_callbacks.py'
        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: python.to_type(variable_type)
        dtig_parser.to_proto_message = lambda variable_type: python.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'f\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)

class ServerGeneratorCMD(ServerGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)
        self.output_file += "_server.py"

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        self.engine_template_file = f'{template_folder}/server_callbacks.py'

        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: python.to_type(variable_type)
        dtig_parser.to_proto_message = lambda variable_type: python.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'f\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)