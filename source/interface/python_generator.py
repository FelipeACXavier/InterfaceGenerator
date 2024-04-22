import os
import subprocess

import json

from tools import python

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
        self.function_definition = lambda name, args: f'def {name}({args}):'

        # First groups must be the function name and the second group should be the arguments
        self.comment_char = fr'#'
        self.function_regex = fr'def(.*)\((.*)\).*:'

        self.callbacks = python.create_structure()

    def read_templates(self) -> VoidResult:
        self.common_template_file = engine_folder + \
            "/templates/python_server_template.py"

        LOG_DEBUG(f'Parsing common template: {self.common_template_file}')
        formatting = python.format(self.common_template_file)
        if not formatting.is_success():
            return formatting

        # First, parse the common interface template
        data = python.read_file(self.common_template_file)

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
            data, KEY_PARSE, has_argument=True, maximum=NUMBER_OF_MESSAGES)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read parse: {result}')

        # Callbacks can be overwritten by each engine, but by parsing them here, we at least ensure that they exist
        result = self.parse_template(
                data, KEY_CALLBACK, has_argument=True, maximum=NUMBER_OF_MESSAGES)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read callbacks: {result}')

        # Then parse the engine template
        if self.engine_template_file:
            LOG_DEBUG(f'Parsing engine template: {self.engine_template_file}')
            # formatting = python.format(self.engine_template_file)
            if not formatting.is_success():
                return formatting

            data = python.read_file(self.engine_template_file)

            result = self.parse_template(
                data, KEY_CLASS_NAME, has_argument=False, maximum=1)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read classname: {result}')

            result = self.parse_template(
                data, KEY_CALLBACK, has_argument=True, maximum=None)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read callback file: {result}')

            result = self.parse_template(
                data, KEY_METHOD, has_argument=False, maximum=None)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read method: {result}')

        return super().read_templates()

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
        file_contents += python.set_indentation(creation.value(), level=1)

        # Generate message handler
        creation = self.generate_message_handler()
        if not creation.is_success():
            return creation
        file_contents += python.set_indentation(creation.value(), level=1)

        # Generate main
        creation = self.generate_main()
        if not creation.is_success():
            return creation
        file_contents += creation.value()

        file_contents = self.replace_calls(file_contents)

        with open(self.output_file, "w") as file:
            file.write(file_contents)

        return python.format(self.output_file)

    def generate_class(self) -> Result:
        if self.callbacks[KEY_CLASS_NAME][KEY_BODY]:
            return Result("\nclass " + self.callbacks[KEY_CLASS_NAME][KEY_BODY] + ":")

        return Result("")

    def generate_constructor(self) -> Result:
        body = ""
        for key, access in self.callbacks[KEY_CONSTRUCTOR].items():
            if access[KEY_BODY]:
                body += python.set_indentation(access[KEY_BODY], level=1)

        if self.callbacks[KEY_CALLBACK][KEY_CONSTRUCTOR][KEY_BODY]:
            body += python.set_indentation(self.callbacks[KEY_CALLBACK][KEY_CONSTRUCTOR][KEY_BODY], level=2)

        return Result(body)

    def generate_destructor(self) -> Result:
        body = ""
        for key, access in self.callbacks[KEY_DESTRUCTOR].items():
            if access[KEY_BODY]:
                body += python.set_indentation(access[KEY_BODY], level=1)

        if self.callbacks[KEY_CALLBACK][KEY_DESTRUCTOR][KEY_BODY]:
            body += python.set_indentation(self.callbacks[KEY_CALLBACK][KEY_DESTRUCTOR][KEY_BODY], level=2)

        return Result(body)

    def name_from_key(self, groups):
        name = groups[0]
        args = groups[1]
        callback = groups[2]

        if callback:
            if self.is_valid_callback(callback):
                if self.callbacks[name][callback][KEY_NAME]:
                    return f'self.{self.callbacks[name][callback][KEY_NAME]}'
                else:
                    return f'self.{self.callbacks[name][callback][KEY_BODY]}'
            else:
                return  f'self.{self.callbacks[name][KEY_NAME]}{args}'
        else:
            if self.is_valid_callback(name):
                return f'{self.callbacks[name][KEY_NAME]}{args if args else ""}'
            elif self.is_valid_key(name):
                return f'{self.callbacks[name][KEY_BODY]}{args if args else ""}'
            else:
                return f'{self.callbacks[KEY_NEW][name][KEY_NAME]}{args if args else ""}'

    def function_from_key(self, groups, default_name):
        function_id = groups[1].strip() if default_name is None else default_name
        function_args = groups[2].strip()

        if KEY_SELF not in function_args:
            function_args = ("self, " + function_args).strip().rstrip(",")

        return function_id, function_args

# =======================================================================
# Client generator
#
# Base class used to create common interface clients in python
# =======================================================================
class ClientGenerator(GeneratorBase):
    def __init__(self, output_file):
       super().__init__(output_file)

    def generate(self, config: ModelConfigurationBase) -> VoidResult:
        return VoidResult.failed("Not implemented")

