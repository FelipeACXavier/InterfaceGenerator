import os
import subprocess

import json

from dtig.tools import python

from dtig.common.keys import *
from dtig.common.result import *
from dtig.common.logging import *
from dtig.base.generator_base import GeneratorBase
from dtig.common.model_configuration_base import ModelConfigurationBase

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)


class ServerGenerator(GeneratorBase):
    def __init__(self):
        super().__init__()

        # Set the function definition
        self.function_definition = lambda name, args: f'def {name}({args}):'

        # First groups must be the function name and the second group should be the arguments
        self.function_regex = fr'def(.*)\((.*)\).*:'

    def read_templates(self) -> VoidResult:
        self.common_template_file = engine_folder + \
            "/templates/python_server_template.py"
        python.format(self.common_template_file)

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
            data, KEY_PARSE, has_argument=True, maximum=7)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read parse: {result}')

        LOG_DEBUG(f'Parsing engine template: {self.engine_template_file}')
        formatting = python.format(self.engine_template_file)
        if not formatting.is_success():
            return formatting

        # Then parse the engine template
        data = python.read_file(self.engine_template_file)

        result = self.parse_template(
            data, KEY_CALLBACK, has_argument=True, maximum=10)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read callback file: {result}')

        # print(json.dumps(self.callbacks, indent=2))
        return VoidResult()

    def generate(self, output_file: str, config: ModelConfigurationBase) -> VoidResult:
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

        with open(output_file, "w") as file:
            file.write(file_contents)

        return python.format(output_file)

    def generate_imports(self) -> Result:
        return Result(self.callbacks[KEY_IMPORTS][KEY_BODY] + self.callbacks[KEY_CALLBACK][KEY_IMPORTS][KEY_BODY])

    def generate_states(self) -> Result:
        return Result(self.callbacks[KEY_STATES][KEY_BODY])

    def generate_class(self) -> Result:
        return Result("\nclass " + self.callbacks[KEY_CLASS_NAME][KEY_NAME] + ":")

    def generate_constructor(self) -> Result:
        return Result(
            python.set_indentation(
                self.callbacks[KEY_CONSTRUCTOR][KEY_BODY], level=1)
            + python.set_indentation(self.callbacks[KEY_CALLBACK][KEY_CONSTRUCTOR][KEY_BODY], level=2))

    def generate_destructor(self) -> Result:
        return Result(python.set_indentation(self.callbacks[KEY_DESTRUCTOR][KEY_BODY]
                      + self.callbacks[KEY_CALLBACK][KEY_DESTRUCTOR][KEY_BODY]))

    def generate_message_handler(self) -> Result:
        body = self.callbacks[KEY_MESSAGE_HANDLER][KEY_BODY] + \
            self.generate_message_parsers()
        return Result(python.set_indentation(body))

    def generate_run(self) -> Result:
        body = self.callbacks[KEY_RUN][KEY_BODY] + self.callbacks[KEY_CALLBACK][KEY_RUN][KEY_BODY] + self.callbacks[KEY_RUN_SERVER][KEY_BODY]

        for method in self.callbacks[KEY_METHOD][KEY_BODY]:
            body += method

        return Result(python.set_indentation(body))

    def generate_main(self) -> Result:
        return Result(self.callbacks[KEY_MAIN][KEY_BODY])

    def generate_message_parsers(self) -> str:
        body = str()
        for key, method in self.callbacks[KEY_PARSE].items():
            body += method[KEY_BODY] + self.callbacks[KEY_CALLBACK][key][KEY_BODY]

        return body

    def name_from_key(self, name, callback):
        if callback:
            if self.is_valid_key(callback):
                return f'self.{self.callbacks[name][callback][KEY_NAME]}'
            else:
                return  f'self.{self.callbacks[name][KEY_NAME]}({callback})'
        else:
            return f'{self.callbacks[name][KEY_NAME]}()'

    def arguments_from_key(self, arguments):
        if KEY_SELF not in arguments:
            return "self, " + arguments

        return arguments


# =======================================================================
# Client generator
#
# Base class used to create common interface clients in python
# =======================================================================
class ClientGenerator(GeneratorBase):
    def __init__(self):
        self.callbacks = {
            "stop": {KEY_NAME: "stop_callback", KEY_BODY: "pass"},
            "start": {KEY_NAME: "start_callback", KEY_BODY: "pass"},
            "set_input": {KEY_NAME: "set_input_callback", KEY_BODY: "pass"},
            "get_output": {KEY_NAME: "get_output_callback", KEY_BODY: "pass"},
            "advance": {KEY_NAME: "advance_callback", KEY_BODY: "pass"},
            "initialize": {KEY_NAME: "initialize_callback", KEY_BODY: "pass"},
        }

    def generate(self, output_file: str, config: ModelConfigurationBase) -> VoidResult:
        return VoidResult.failed("Not implemented")

