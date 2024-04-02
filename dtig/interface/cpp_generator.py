import os
import json

from pathlib import Path
from dtig.tools import cpp

from dtig.common.keys import *
from dtig.common.result import *
from dtig.common.logging import *
from dtig.base.generator_base import GeneratorBase
from dtig.common.model_configuration_base import ModelConfigurationBase

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)
cpp_function_regex=fr'^([A-Za-z_:1-9\s<>]*?)([\/@~A-Za-z_1-9]+)\(([\S\s]*?)\)'

class HppGenerator(GeneratorBase):
    def __init__(self, output_file):
        super().__init__(output_file)

        # Set the function definition
        self.function_definition = lambda name, args: f'{name}({args})'

        # First groups must be the function name and the second group should be the arguments
        self.function_regex = cpp_function_regex
        self.comment_char = fr'\/\/'

    def read_templates(self) -> VoidResult:
        if self.common_template_file is None:
            self.common_template_file = engine_folder + "/templates/cpp_template.h"

        LOG_DEBUG(f'Parsing common template: {self.common_template_file}')

        # First, parse the common interface template
        data = cpp.read_file(self.common_template_file)

        result = self.parse_template(
            data, KEY_NEW, has_argument=True, maximum=None)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read new: {result}')

        result = self.parse_template(
            data, KEY_CLASS_NAME, has_argument=False, maximum=None)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read classname: {result}')

        result = self.parse_template(
            data, KEY_MAIN, has_argument=False, maximum=1)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read main: {result}')

        result = self.parse_template(
            data, KEY_INHERIT, has_argument=False, maximum=None)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read inherit: {result}')

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
            data, KEY_MEMBER, has_argument=False, maximum=None)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read member: {result}')

        result = self.parse_template(
            data, KEY_PARSE, has_argument=True, maximum=8)
        if not result.is_success():
            return VoidResult.failed(f'Failed to read parse: {result}')

        LOG_DEBUG(f'Parsing engine template: {self.engine_template_file}')

        # Then parse the engine template
        if self.engine_template_file:
            data = cpp.read_file(self.engine_template_file)

            result = self.parse_template(
                data, KEY_CALLBACK, has_argument=True, maximum=10)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read engine callback: {result}')

            result = self.parse_template(
                data, KEY_MEMBER, has_argument=False, maximum=None)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read engine member: {result}')

            result = self.parse_template(
                data, KEY_METHOD, has_argument=False, maximum=None)
            if not result.is_success():
                return VoidResult.failed(f'Failed to read engine method: {result}')

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

        if self.callbacks[KEY_CLASS_NAME][KEY_BODY]:
            file_contents += "};\n"

        file_contents = self.replace_calls(file_contents)

        with open(self.output_file, "w") as file:
            file.write(cpp.set_indentation(file_contents))

        return VoidResult()

    def generate_imports(self) -> Result:
        body = "#pragma once\n"
        generated = super().generate_imports()
        if generated:
            body += generated.value()

        return Result(body)

    def generate_class(self) -> Result:
        if self.callbacks[KEY_CLASS_NAME][KEY_BODY]:
            inheritance = self.generate_inherit()
            if not inheritance:
                return inheritance

            inherit_string = "" if len(inheritance.value()) < 1 else f':{inheritance.value()}'
            return Result(f'\nclass {self.callbacks[KEY_CLASS_NAME][KEY_BODY]}{inherit_string}\n{{')

        return Result("")

    def generate_run(self) -> Result:
        body = ""

        if self.callbacks[KEY_CONSTRUCTOR][KEY_PUBLIC][KEY_BODY] \
            or self.callbacks[KEY_DESTRUCTOR][KEY_PUBLIC][KEY_BODY] \
            or self.callbacks[KEY_METHOD][KEY_PUBLIC][KEY_BODY]\
            or self.callbacks[KEY_MEMBER][KEY_PUBLIC][KEY_BODY]:
            body += "\npublic:\n"

        if self.callbacks[KEY_CONSTRUCTOR][KEY_PUBLIC][KEY_BODY]:
            LOG_INFO(f'Adding: {self.callbacks[KEY_CONSTRUCTOR][KEY_PUBLIC][KEY_BODY]}')
            body += self.callbacks[KEY_CONSTRUCTOR][KEY_PUBLIC][KEY_BODY]

        if self.callbacks[KEY_DESTRUCTOR][KEY_PUBLIC][KEY_BODY]:
            body += self.callbacks[KEY_DESTRUCTOR][KEY_PUBLIC][KEY_BODY]

        for member in self.callbacks[KEY_MEMBER][KEY_PUBLIC][KEY_BODY]:
            body += member
        for method in self.callbacks[KEY_METHOD][KEY_PUBLIC][KEY_BODY]:
            body += method

        if self.callbacks[KEY_RUN][KEY_BODY]:
            body += self.callbacks[KEY_RUN][KEY_BODY]

        if self.callbacks[KEY_CALLBACK][KEY_RUN_MODEL][KEY_BODY]:
            body += self.callbacks[KEY_CALLBACK][KEY_RUN_MODEL][KEY_BODY]

        if self.callbacks[KEY_RUN_SERVER][KEY_BODY]:
            body += self.callbacks[KEY_RUN_SERVER][KEY_BODY]

        if self.callbacks[KEY_CONSTRUCTOR][KEY_PRIVATE][KEY_BODY] \
            or self.callbacks[KEY_CONSTRUCTOR][KEY_PRIVATE][KEY_BODY] \
            or self.callbacks[KEY_METHOD][KEY_PRIVATE][KEY_BODY] \
            or self.callbacks[KEY_MEMBER][KEY_PRIVATE][KEY_BODY]:
            body += "\nprivate:\n"

        if self.callbacks[KEY_CONSTRUCTOR][KEY_PRIVATE][KEY_BODY]:
            body += self.callbacks[KEY_CONSTRUCTOR][KEY_PRIVATE][KEY_BODY]

        if self.callbacks[KEY_DESTRUCTOR][KEY_PRIVATE][KEY_BODY]:
            body += self.callbacks[KEY_DESTRUCTOR][KEY_PRIVATE][KEY_BODY]

        for member in self.callbacks[KEY_MEMBER][KEY_PRIVATE][KEY_BODY]:
            body += member
        for method in self.callbacks[KEY_METHOD][KEY_PRIVATE][KEY_BODY]:
            body += method

        return Result(body)

    def generate_inherit(self) -> Result:
        body = ""

        for name in self.callbacks[KEY_INHERIT][KEY_PUBLIC][KEY_BODY]:
            body += f' public {name},'

        for name in self.callbacks[KEY_INHERIT][KEY_PRIVATE][KEY_BODY]:
            body += f' private {name},'

        return Result(body.rstrip(","))

    def generate_message_parsers(self) -> Result:
        body = ""
        for key, method in self.callbacks[KEY_PARSE].items():
            if method[KEY_BODY]:
                body += method[KEY_BODY]

        return Result(body)

    def name_from_key(self, groups):
        name = groups[0]
        args = groups[1]
        callback = groups[2]

        if callback:
            if self.is_valid_callback(callback):
                if self.callbacks[name][callback][KEY_BODY]:
                    return f'{self.callbacks[name][callback][KEY_BODY]}'
                elif self.callbacks[name][callback][KEY_NAME]:
                    return f'{self.callbacks[name][callback][KEY_NAME]}'
                else:
                    return ""
            else:
                return  f'{self.callbacks[name][KEY_BODY]}{args}'
        else:
            if self.is_valid_callback(name):
                return f'{self.callbacks[KEY_CALLBACK][name][KEY_NAME]}{args if args else ""}'
            elif self.is_valid_key(name):
                return f'{self.callbacks[name][KEY_BODY]}{args if args else ""}'
            else:
                return f'{self.callbacks[KEY_NEW][name][KEY_BODY]}{args if args else ""}'

    def function_from_key(self, groups, default_name):
        ctype = groups.groups()[0].strip()
        name = groups.groups()[1].strip() if default_name is None else default_name
        args = groups.groups()[2].strip()

        if len(ctype) > 0:
            function_id = f'{ctype} {name}'
        else:
            function_id = f'{name}'

        function_args = args
        return function_id, function_args

class CppGenerator(GeneratorBase):
    def __init__(self, output_file, header_name = None):
        super().__init__(output_file)

        self.header_name = header_name
        if self.header_name and ".h" not in self.header_name and ".hpp" not in self.header_name:
            self.header_name += ".h"

        # Set the function definition
        self.function_definition = lambda name, args: f'{name}({args})'

        # First groups must be the function name and the second group should be the arguments
        self.function_regex = cpp_function_regex
        self.comment_char = fr'\/\/'

    def read_templates(self) -> VoidResult:
        if not self.common_template_file:
            self.common_template_file = engine_folder + "/templates/cpp_template.cpp"

        LOG_DEBUG(f'Parsing common template: {self.common_template_file}')

        # First, parse the common interface template
        data = cpp.read_file(self.common_template_file)

        result = self.parse_template(
            data, KEY_CLASS_NAME, has_argument=False, maximum=None)
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
            data = cpp.read_file(self.engine_template_file)

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

        with open(self.output_file, "w") as file:
            file.write(self.replace_calls(file_contents))

        # Create main file if @main is defined
        if self.callbacks[KEY_MAIN][KEY_BODY]:
            main_file = os.path.dirname(self.output_file) + "/main.cpp"

            LOG_DEBUG(f'Writing main file to {main_file}')
            with open(main_file, "w") as file:
                creation = self.generate_main()
                if not creation.is_success():
                    return creation

                file.write(self.replace_calls(creation.value()))

        return VoidResult()

    def generate_imports(self) -> Result:
        body = ""
        if self.header_name:
            body = f'#include "{self.header_name}"\n'

        generated = super().generate_imports()
        if generated:
            body += generated.value()

        return Result(body)

    def generate_class(self) -> Result:
        if self.callbacks[KEY_CLASS_NAME][KEY_NAME]:
            return Result("\nclass " + self.callbacks[KEY_CLASS_NAME][KEY_NAME] + "{")

        return Result("")

    def generate_main(self) -> Result:
        body = ""
        if self.header_name:
            body = f'#include "{self.header_name}"\n'

        generated = super().generate_main()
        if generated:
            body += generated.value()

        return Result(body)

    def function_from_key(self, groups, default_name):
        ctype = groups.groups()[0].strip()
        name = groups.groups()[1].strip() if default_name is None else default_name
        args = groups.groups()[2].strip()

        function_id = f'{ctype} // @>{KEY_CLASS_NAME}::{name}'

        function_args = args
        return function_id, function_args

