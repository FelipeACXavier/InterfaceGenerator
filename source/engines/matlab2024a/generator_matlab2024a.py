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
        template_dir = f'{Path(self.output_file).parent.absolute()}/templates'
        file_system.create_dir(template_dir)

        self.engine_template_file = f'{template_dir}/matlab_callbacks.m'

        self.generate_model_config(engine_folder + "/matlab_callbacks.m")

        return super().generate(config)

    def generate_model_config(self, input_file):
        body = ""

        # Store current state of the callback files
        with open(input_file, "r") as f:
            body = f.read() + "\n"

        body += self.generate_model_members()
        body += self.generate_model_set_input()
        body += self.generate_model_get_output()
        body += self.generate_model_set_parameter()
        body += self.generate_model_get_parameter()

        with open(self.engine_template_file, "w") as f:
            f.write(body)

    def generate_model_members(self) -> str:
        body = f'% @callback({KEY_IMPORTS})\n'
        if self.config.has(KEY_INPUTS):
            body += f'% Inputs\n'
            body += f'global '
            for cfg in self.config[KEY_INPUTS]:
                body += f'{cfg[KEY_NAME]} '
            body = body.rstrip() + f';\n\n'

        if self.config.has(KEY_OUTPUTS):
            body += f'% Outputs\n'
            body += f'global '
            for cfg in self.config[KEY_OUTPUTS]:
                body += f'{cfg[KEY_NAME]} '
            body = body.rstrip() + f';\n\n'

        if self.config.has(KEY_PARAMETERS):
            body += f'% Parameters\n'
            body += f'global '
            for cfg in self.config[KEY_PARAMETERS]:
                body += f'{cfg[KEY_NAME]} '
            body = body.rstrip() + f';\n\n'

        return body

    def generate_model_set_input(self) -> str:
        body = f'\n% @callback({KEY_SET_INPUT})\n'
        body += "function returnValue = set_inputs(reference, anyValue)\n"

        if not self.config.has(KEY_INPUTS) or not len(self.config[KEY_INPUTS]):
            body += f'\treturnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no inputs");\n'
            return body

        variables = f'\tglobal '
        for cfg in self.config[KEY_INPUTS]:
            variables += f'{cfg[KEY_NAME]} '
        body += f'{variables.rstrip()};\n\n'

        # Check that the reference is valid
        body += f'\tvalue = dtig.Helpers.unpack(anyValue);\n'
        body += f'\tif isempty(value)\n'
        body += f'\t\treturnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));\n'
        body += f'\t\treturn;\n'
        body += f'\tend\n\n'

        for i, cfg in enumerate(self.config[KEY_INPUTS]):
            body += f'\t{"if" if i == 0 else "elseif"} reference == "{cfg[KEY_NAME]}"\n'
            body += f'\t\t{cfg[KEY_NAME]} = value.getValue();\n'
        body += f'\telse\n'
        body += f'\t\treturnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));\n'
        body += f'\t\treturn;\n'
        body += f'\tend\n\n'
        body += f'\treturnValue = createReturn(dtig.EReturnCode.SUCCESS);\n'
        # End function
        body += f'end'

        return body

    def generate_model_get_output(self) -> str:
        body = f'\n% @callback({KEY_GET_OUTPUT})\n'
        body += "function returnValue = get_outputs(references)\n"

        if not self.config.has(KEY_OUTPUTS) or not len(self.config[KEY_OUTPUTS]):
            body += f'\treturnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no outputs");\n'
            return body

        variables = f'\tglobal '
        for cfg in self.config[KEY_OUTPUTS]:
            variables += f'{cfg[KEY_NAME]} '
        body += f'{variables.rstrip()};\n\n'

        body += f'\tdtigOutputs = dtig.MValues.newBuilder();\n'
        body += f'\tnIds = references.size() - 1;\n'

        body += f'\treturnValue = createReturn(dtig.EReturnCode.SUCCESS);\n'
        body += f'\tfor i = 0:nIds\n'
        body += f'\t\treference = references.get(i);\n'
        body += f'\t\tdtigOutputs.addIdentifiers(reference);\n'

        for i, cfg in enumerate(self.config[KEY_OUTPUTS]):
            body += f'\t\t{"if" if i == 0 else "elseif"} reference == "{cfg[KEY_NAME]}"\n'
            body += f'\t\t\tanyValue = {matlab.to_proto_message(cfg["type"])}.newBuilder().setValue({cfg[KEY_NAME]});\n'

        body += f'\t\telse\n'
        body += f'\t\t\treturnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown output: ", reference));\n'
        body += f'\t\t\treturn;\n'
        body += f'\t\tend\n\n'

        body += f'\t\tdtigOutputs.addValues(dtig.Helpers.pack(anyValue));\n'

        #  End for
        body += f'\tend\n'
        body += f'\treturnValue.setValues(dtigOutputs);\n'

        # End function
        body += f'end'

        return body

    def generate_model_set_parameter(self) -> str:
        body = f'\n% @callback({KEY_SET_PARAMETER})\n'
        body += "function returnValue = set_parameter(reference, anyValue)\n"

        if not self.config.has(KEY_PARAMETERS) or not len(self.config[KEY_PARAMETERS]):
            body += f'\treturnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no parameters");\n'
            return body

        variables = f'\tglobal '
        for cfg in self.config[KEY_PARAMETERS]:
            variables += f'{cfg[KEY_NAME]} '
        body += f'{variables.rstrip()};\n\n'

        # Check that the reference is valid
        body += f'\tvalue = dtig.Helpers.unpack(anyValue);\n'
        body += f'\tif isempty(value)\n'
        body += f'\t\treturnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));\n'
        body += f'\t\treturn;\n'
        body += f'\tend\n\n'

        for i, cfg in enumerate(self.config[KEY_PARAMETERS]):
            body += f'\t{"if" if i == 0 else "elseif"} reference == "{cfg[KEY_NAME]}"\n'
            body += f'\t\t{cfg[KEY_NAME]} = value.getValue();\n'
        body += f'\telse\n'
        body += f'\t\treturnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown parameter: ", reference));\n'
        body += f'\t\treturn;\n'
        body += f'\tend\n\n'
        body += f'\treturnValue = createReturn(dtig.EReturnCode.SUCCESS);\n'

        # End function
        body += f'end'

        return body

    def generate_model_get_parameter(self) -> str:
        body = f'\n% @callback({KEY_GET_PARAMETER})\n'
        body += "function returnValue = get_outputs(references)\n"

        if not self.config.has(KEY_PARAMETERS) or not len(self.config[KEY_PARAMETERS]):
            body += f'\treturnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no parameters");\n'
            return body

        variables = f'\tglobal '
        for cfg in self.config[KEY_PARAMETERS]:
            variables += f'{cfg[KEY_NAME]} '
        body += f'{variables.rstrip()};\n\n'

        body += f'\tdtigOutputs = dtig.MValues.newBuilder();\n'
        body += f'\tnIds = references.size() - 1;\n'

        body += f'\treturnValue = createReturn(dtig.EReturnCode.SUCCESS);\n'
        body += f'\tfor i = 0:nIds\n'
        body += f'\t\treference = references.get(i);\n'
        body += f'\t\tdtigOutputs.addIdentifiers(reference);\n'

        for i, cfg in enumerate(self.config[KEY_PARAMETERS]):
            body += f'\t\t{"if" if i == 0 else "elseif"} reference == "{cfg[KEY_NAME]}"\n'
            body += f'\t\t\tanyValue = {matlab.to_proto_message(cfg["type"])}.newBuilder().setValue({cfg[KEY_NAME]});\n'

        body += f'\t\telse\n'
        body += f'\t\t\treturnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown parameter: ", reference));\n'
        body += f'\t\t\treturn;\n'
        body += f'\t\tend\n\n'

        body += f'\t\tdtigOutputs.addValues(dtig.Helpers.pack(anyValue));\n'

        #  End for
        body += f'\tend\n'

        body += f'\treturnValue.setValues(dtigOutputs);\n'

        # End function
        body += f'end'

        return body
