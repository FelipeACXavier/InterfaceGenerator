import os

from tools import python
from common.keys import *
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
        self.engine_template_file = os.path.dirname(self.output_file) + "/server_callbacks.py"

        self.generate_model_config(engine_folder + "/server_callbacks.py")

        return super().generate(config)

    def generate_model_config(self, input_file):
        body = ""

        # Store current state of the callback files
        with open(input_file, "r") as f:
            body = f.read()

        body += self.generate_model_set_input()
        body += self.generate_model_get_output()
        body += self.generate_model_set_parameter()
        body += self.generate_model_get_parameter()

        with open(self.engine_template_file, "w") as f:
            f.write(body)

    def generate_model_set_input(self) -> str:
        body = f'\n# @callback({KEY_SET_INPUT})\n'
        body += "def set_inputs(reference, any_value):\n"

        if not self.config.has(KEY_INPUTS) or not len(self.config[KEY_INPUTS]):
            body += f'\treturn self.return_code(dtig_code.FAILURE, "Model has no inputs")\n'
            return body

        # Check that the reference is valid
        body += f'\tif not reference in self.value_references:\n'
        body += f'\t\treturn self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown input: {{reference}}")\n\n'

        for i, cfg in enumerate(self.config[KEY_INPUTS]):
            body += f'\t{"if" if i == 0 else "elif"} reference == "{cfg[KEY_NAME]}":\n'
            body += f'\t\tvalue = {python.to_proto_message(cfg["type"])}\n'

            body += f'\t\tif not any_value.Unpack(value):\n'
            body += f'\t\t\treturn self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {{reference}}")\n\n'

            body += f'\t\tself.fmu.set{self.type_to_fmi_function(cfg["type"])}([self.value_references[reference]], [value.value])\n\n'

        body += f'\treturn self.return_code(dtig_code.SUCCESS)\n'

        return body


    def generate_model_get_output(self) -> str:
        body = f'\n# @callback({KEY_GET_OUTPUT})\n'
        body += "def get_outputs(references):\n"

        if not self.config.has(KEY_OUTPUTS) or not len(self.config[KEY_OUTPUTS]):
            body += f'\treturn self.return_code(dtig_code.FAILURE, "Model has no outputs")\n'
            return body

        body += f'\treturn_message = self.return_code(dtig_code.SUCCESS)\n'
        body += f'\tfor reference in references:\n'
        body += '\t\tif not reference in self.value_references:\n'
        body += '\t\t\treturn self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")\n\n'
        for i, cfg in enumerate(self.config[KEY_OUTPUTS]):
            body += f'\t\t{"if" if i == 0 else "elif"} reference == "{cfg[KEY_NAME]}":\n'
            body += f'\t\t\tany_value = {python.to_proto_message(cfg["type"])}\n'
            body += f'\t\t\tany_value.value = self.fmu.get{self.type_to_fmi_function(cfg["type"])}([self.value_references[reference]])[0]\n'

        body += f'\n\t\tany_msg = any_pb2.Any()\n'
        body += f'\t\tany_msg.Pack(any_value)\n\n'
        body += f'\t\treturn_message.values.identifiers.append(reference)\n'
        body += f'\t\treturn_message.values.values.append(any_msg)\n\n'

        body += f'\treturn return_message\n'

        return body


    def generate_model_set_parameter(self) -> str:
        body = f'\n# @callback({KEY_SET_PARAMETER})\n'
        body += "def set_parameters(reference, any_value):\n"

        if not self.config.has(KEY_PARAMETERS) or not len(self.config[KEY_PARAMETERS]):
            body += f'\treturn self.return_code(dtig_code.FAILURE, "Model has no parameters")\n'
            return body

        # Check that the reference is valid
        body += f'\tif not reference in self.value_references:\n'
        body += f'\t\treturn self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown parameter: {{reference}}")\n\n'

        for i, cfg in enumerate(self.config[KEY_PARAMETERS]):
            body += f'\t{"if" if i == 0 else "elif"} reference == "{cfg[KEY_NAME]}":\n'
            body += f'\t\tvalue = {python.to_proto_message(cfg["type"])}\n'

            body += f'\t\tif not any_value.Unpack(value):\n'
            body += f'\t\t\treturn self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {{reference}}")\n\n'

            body += f'\t\tself.fmu.set{self.type_to_fmi_function(cfg["type"])}([self.value_references[reference]], [value.value])\n\n'

        body += f'\treturn self.return_code(dtig_code.SUCCESS)\n'

        return body

        return body


    def generate_model_get_parameter(self) -> str:
        body = f'\n# @callback({KEY_GET_PARAMETER})\n'
        body += "def get_parameters(references):\n"

        if not self.config.has(KEY_PARAMETERS) or not len(self.config[KEY_PARAMETERS]):
            body += f'\treturn self.return_code(dtig_code.FAILURE, "Model has no parameters")\n'
            return body

        body += f'\treturn_message = self.return_code(dtig_code.SUCCESS)\n'
        body += f'\tfor reference in references:\n'
        body += '\t\tif not reference in self.value_references:\n'
        body += '\t\t\treturn self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown parameter: {reference}")\n\n'
        for i, cfg in enumerate(self.config[KEY_PARAMETERS]):
            func = ""
            body += f'\t\t{"if" if i == 0 else "elif"} reference == "{cfg[KEY_NAME]}":\n'
            body += f'\t\t\tany_value = {python.to_proto_message(cfg["type"])}\n'
            body += f'\t\t\tany_value.value = self.fmu.get{self.type_to_fmi_function(cfg["type"])}([self.value_references[reference]])[0]\n'

        body += f'\n\t\tany_msg = any_pb2.Any()\n'
        body += f'\t\tany_msg.Pack(any_value)\n\n'
        body += f'\t\treturn_message.values.identifiers.append(reference)\n'
        body += f'\t\treturn_message.values.values.append(any_msg)\n\n'

        body += f'\treturn return_message\n'

        return body

    def type_to_fmi_function(self, variable_type):
        if variable_type == TYPE_FLOAT_32:
            return"Real"
        elif variable_type == TYPE_FLOAT_64:
            return"Real"
        elif variable_type == TYPE_INT_32:
            return"Integer"
        elif variable_type == TYPE_INT_64:
            return"Integer"
        elif variable_type == TYPE_UINT_32:
            return"Integer"
        elif variable_type == TYPE_UINT_64:
            return"Integer"
        elif variable_type == TYPE_STRING:
            return"String"
        elif variable_type == TYPE_BOOL:
            return"Boolean"

# =============================================================
# Client generator

class ClientGeneratorFMI2(ClientGenerator):
  def __init__(self, output_file):
    super().__init__(output_file)
    self.output_file += "_client.py"

  def generate(self, config : ModelConfigurationBase) -> VoidResult:
    return VoidResult()