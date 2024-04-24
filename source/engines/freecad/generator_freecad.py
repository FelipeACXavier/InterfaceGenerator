import os
import json

from tools import python
from common.keys import *
from common.result import *
from common.logging import *
from common.model_configuration_base import ModelConfigurationBase

from language import parser

from interface.python_generator import ServerGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)
template_folder = engine_folder + "/templates"

class ServerGeneratorFreeCAD(ServerGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)
        self.output_file += "_server.py"

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        self.engine_template_file = f'{template_folder}/server_callbacks.py'

        return super().generate(config)

    def type_to_freecad_function(self, variable_type):
        if variable_type == TYPE_FLOAT_32:
            return "Real"
        elif variable_type == TYPE_FLOAT_64:
            return "Real"
        elif variable_type == TYPE_INT_32:
            return "Integer"
        elif variable_type == TYPE_INT_64:
            return "Integer"
        elif variable_type == TYPE_UINT_32:
            return "Integer"
        elif variable_type == TYPE_UINT_64:
            return "Integer"
        elif variable_type == TYPE_STRING:
            return "String"
        elif variable_type == TYPE_BOOL:
            return "Boolean"
        elif variable_type == TYPE_FIXTURE:
            return "ObjectsFem.makeConstraintFixed"
        elif variable_type == TYPE_FORCE:
            return "ObjectsFem.makeConstraintForce"
        elif variable_type == f'TYPE_MATERIAL':
            return "ObjectsFem.makeMaterialSolid"

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: self.type_to_freecad_function(variable_type)
        dtig_parser.to_proto_message = lambda variable_type: python.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'f\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)

