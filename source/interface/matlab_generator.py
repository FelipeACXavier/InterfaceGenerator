import os
import json

from pathlib import Path
from tools import matlab

from common.keys import *
from common.result import *
from common.logging import *
from base.generator_base import GeneratorBase
from common.model_configuration_base import ModelConfigurationBase

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGenerator(GeneratorBase):
    def __init__(self, output_file):
        super().__init__(output_file)

        # Set the function definition
        self.function_definition = lambda name, args: f'function {name}({args})'

        # First groups must be the function name and the second group should be the arguments
        self.function_regex = fr'^function ([\/@~A-Za-z_1-9]+)\(([\S\s]*?)\)'
        self.comment_char = fr'%'

    def read_templates(self) -> VoidResult:
        self.common_template_file = engine_folder + \
            "/templates/matlab_server_template.m"

        LOG_DEBUG(f'Parsing common template: {self.common_template_file}')

        # First, parse the common interface template
        data = matlab.read_file(self.common_template_file)

        result = self.parse_template(
            data, KEY_CLASS_NAME, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read classname: {result}')

        result = self.parse_template(
            data, KEY_MAIN, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read main: {result}')

        result = self.parse_template(
            data, KEY_CONSTRUCTOR, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read constructor: {result}')

        result = self.parse_template(
            data, KEY_DESTRUCTOR, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read destructor: {result}')

        result = self.parse_template(
            data, KEY_IMPORTS, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read imports: {result}')

        result = self.parse_template(
            data, KEY_STATES, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read states: {result}')

        result = self.parse_template(
            data, KEY_RUN, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read run: {result}')

        result = self.parse_template(
            data, KEY_RUN_SERVER, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read runserver: {result}')

        result = self.parse_template(
            data, KEY_MESSAGE_HANDLER, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read messagehandler: {result}')

        result = self.parse_template(
            data, KEY_METHOD, has_argument=False, maximum=None)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read method: {result}')

        result = self.parse_template(
            data, KEY_PARSE, has_argument=True, maximum=8)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read parse: {result}')

        LOG_DEBUG(f'Parsing engine template: {self.engine_template_file}')

        # Then parse the engine template
        if self.engine_template_file:
            data = matlab.read_file(self.engine_template_file)

            result = self.parse_template(
                data, KEY_CALLBACK, has_argument=True, maximum=10)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read callback file: {result}')

            result = self.parse_template(
                data, KEY_METHOD, has_argument=False, maximum=None)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read method: {result}')

        return VoidResult()

    def generate(self, config: ModelConfigurationBase) -> VoidResult:
        reading_templates = self.read_templates()
        if not reading_templates.is_success():
            return reading_templates

        file_contents = str()

        # Generate imports
        creation = self.generate_imports()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate states
        creation = self.generate_states()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate class
        creation = self.generate_class()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate constructor
        creation = self.generate_constructor()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate destructor
        creation = self.generate_destructor()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate run
        creation = self.generate_run()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate message handler
        creation = self.generate_message_handler()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        # Generate main
        creation = self.generate_main()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        file_contents = self.replace_calls(file_contents)

        with open(self.output_file, "w") as file:
            file.write(file_contents)

        return VoidResult()

    def generate_class(self) -> Result:
        if self.callbacks[KEY_CLASS_NAME][KEY_NAME]:
            return Result("\nclass " + self.callbacks[KEY_CLASS_NAME][KEY_NAME] + ":")

        return Result("")

    def name_from_key(self, groups):
        name = groups[0]
        args = groups[1]
        callback = groups[2]

        if callback:
            if self.is_valid_callback(callback):
                return f'self.{self.callbacks[name][callback][KEY_NAME]}'
            else:
                return f'self.{self.callbacks[name][KEY_NAME]}{args}'
        else:
            if name in self.callbacks:
                return f'{self.callbacks[name][KEY_NAME]}{args if args else ""}'
            else:
                return f'{self.callbacks[KEY_NEW][name][KEY_NAME]}{args if args else ""}'

    def function_from_key(self, groups, default_name):
        function_id = groups[1].strip() if default_name is None else default_name
        function_args = groups[2].strip()

        if KEY_SELF not in function_args:
            function_args = ("self, " + function_args).strip().rstrip(",")

        return function_id, function_args
