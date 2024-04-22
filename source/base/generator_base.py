import re
import json

from pathlib import Path
from abc import abstractmethod

from common.keys import *
from common.logging import *
from common.result import Result, VoidResult
from common.default_structure import create_default_structure
from common.model_configuration_base import ModelConfigurationBase

class GeneratorBase():
    # Must be called from any children so members are initialized
    def __init__(self, output_file):
        self.config = None

        self.output_file = output_file

        self.comment_char = None
        self.engine_template_file = None
        self.common_template_file = None

        self.function_regex = None
        self.function_definition = None
        self.callbacks = create_default_structure()

        self.dtig_parser = None

    def new_callback(self, key, data):
        self.callbacks[KEY_NEW][key] = data

    def get_output_file(self):
        return self.output_file

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        raise Exception("Not implemented")

    def read_templates(self) -> VoidResult:
        self.parse_dtig_language()
        return VoidResult()

    def parse_template(self, data, name: str, has_argument: bool = False, maximum: int = None) -> VoidResult:
        if not self.comment_char:
            return VoidResult.failed("No comment character defined")

        # Look for the decorators
        # regex = fr'^{self.comment_char}\s*@({name}\b)(\(([a-z_]*)\))?'
        regex = fr'^<DTIG_({name})\b(\(([A-Z_]*)\))?.*>'
        matches = [m for m in re.finditer(regex, data, flags=re.MULTILINE)]
        # Small sanity checks
        if maximum is not None and len(matches) > maximum:
            return VoidResult.failed(f'Only {maximum} {name} is allowed in the template')

        for match in matches:
            # Get the information from the decorator
            decorator = data[match.start():match.end()]
            decorator_name = match[1]
            decorator_arg = match[3]

            if decorator_name is None or (has_argument and decorator_arg is None):
                return VoidResult.failed(f'{decorator} a group is missing. Name {decorator_name}, Args {decorator_arg}')

            LOG_TRACE(f'{decorator}: {decorator_name} {decorator_arg}')

            function_start = match.end() + 1
            updated_data = data[function_start:]

            # Search for the next decorator
            # @ in the middle of a function are replaced later
            # end = re.search(fr'^{self.comment_char}\s*@(?!>[^\s])', updated_data, flags=re.MULTILINE)
            end = re.search(fr'^\s*<DTIG(?!>[^\s])', updated_data, flags=re.MULTILINE)
            offset = (len(data) - len(updated_data))
            function_end = len(data) - 1 if end is None else end.start() - 1 + offset

            # Remove trailing whitespaces
            while data[function_end] == self.comment_char[0] or data[function_end].isspace():
                function_end -= 1

            body = data[function_start:function_end + 1]

            # Get the name of the function to be used
            callback = self.callbacks[name] if not decorator_arg else self.callbacks[name][decorator_arg]
            callback_name = callback[KEY_NAME]

            if callback[KEY_SELF]:
                definition = re.search(self.function_regex, body)
                if not definition:
                    LOG_WARNING(f'\n{body}')
                    return VoidResult.failed(f'Could not find function definition for: {name}')

                function_id, function_args = self.function_from_key(definition, callback_name)

                LOG_TRACE(f'Function {function_id} with args: {function_args}')
                # Set default callback name
                default = self.function_definition(function_id, function_args)
                body = body[:definition.start()] + default + body[definition.end():]

            # If we are dealing with:
            # KEY_CALLBACK      KEY_PARSE
            # KEY_METHOD        KEY_MEMBER
            # KEY_CONSTRUCTOR   KEY_DESTRUCTOR
            # KEY_INHERIT
            if decorator_arg:
                if name == KEY_INHERIT or name == KEY_MEMBER:
                    self.callbacks[name][decorator_arg][KEY_BODY].append(body)
                elif name == KEY_METHOD:
                    self.callbacks[name][decorator_arg][KEY_BODY].append(f'\n{body}\n')
                else:
                    self.callbacks[name][decorator_arg][KEY_BODY] = f'\n{body}\n'
            else:
                self.callbacks[name][KEY_BODY] = f'\n{body}\n' if self.callbacks[name][KEY_SELF] else f'{body}'

        return VoidResult()

    def replace_calls(self, contents: str):
        iter_body = contents
        # regex = fr'{self.comment_char}\s*@>([a-z_]*\b)(\(([a-z_]*)\))?'
        regex = fr'DTIG>([A-Z_]*\b)(\(([\w_]*)\))?'
        while True:
            match = re.search(regex, iter_body)
            if not match:
                break

            offset = (len(contents) - len(iter_body))
            replacement = self.name_from_key(match.groups())
            # LOG_TRACE(f'Replacing: {match} -> {replacement}')
            contents = contents[:match.start() + offset] + replacement + contents[match.end() + offset:]

            iter_body = iter_body[match.end():]

        return contents

    def is_valid_key(self, key):
        return key and key in self.callbacks.keys()

    def is_valid_callback(self, key):
        return key and (key in self.callbacks[KEY_CALLBACK].keys() \
                        or key == KEY_PRIVATE or key == KEY_PUBLIC)

    def generate_imports(self) -> Result:
        body = ""
        if self.callbacks[KEY_IMPORTS][KEY_BODY]:
            body += self.callbacks[KEY_IMPORTS][KEY_BODY]

        if self.callbacks[KEY_CALLBACK][KEY_IMPORTS][KEY_BODY]:
            body += self.callbacks[KEY_CALLBACK][KEY_IMPORTS][KEY_BODY]


        return Result(body + "\n")

    def generate_states(self) -> Result:
        if self.callbacks[KEY_STATES][KEY_BODY]:
            return Result(self.callbacks[KEY_STATES][KEY_BODY])

        return Result("")

    def generate_class(self) -> Result:
        if self.callbacks[KEY_CLASS_NAME][KEY_BODY]:
            return Result(self.callbacks[KEY_CLASS_NAME][KEY_BODY])

        return Result("")

    def generate_constructor(self) -> Result:
        body = ""
        for key, access in self.callbacks[KEY_CONSTRUCTOR].items():
            if access[KEY_BODY]:
                body += access[KEY_BODY]

        if self.callbacks[KEY_CALLBACK][KEY_CONSTRUCTOR][KEY_BODY]:
            body += self.callbacks[KEY_CALLBACK][KEY_CONSTRUCTOR][KEY_BODY]

        return Result(body)

    def generate_destructor(self) -> Result:
        body = ""
        for key, access in self.callbacks[KEY_DESTRUCTOR].items():
            if access[KEY_BODY]:
                body += access[KEY_BODY]

        if self.callbacks[KEY_CALLBACK][KEY_DESTRUCTOR][KEY_BODY]:
            body += self.callbacks[KEY_CALLBACK][KEY_DESTRUCTOR][KEY_BODY]

        return Result(body)

    def generate_message_handler(self) -> Result:
        body = ""
        if self.callbacks[KEY_MESSAGE_HANDLER][KEY_BODY]:
            body += self.callbacks[KEY_MESSAGE_HANDLER][KEY_BODY]

        generated = self.generate_message_parsers()
        if generated:
            body += generated.value()

        return Result(body)

    def generate_run(self) -> Result:
        body = ""
        if self.callbacks[KEY_RUN][KEY_BODY]:
            body += self.callbacks[KEY_RUN][KEY_BODY]

        if self.callbacks[KEY_RUN_MODEL][KEY_BODY]:
            body += self.callbacks[KEY_RUN_MODEL][KEY_BODY]

        if self.callbacks[KEY_CALLBACK][KEY_RUN_MODEL][KEY_BODY]:
            body += self.callbacks[KEY_CALLBACK][KEY_RUN_MODEL][KEY_BODY]

        if self.callbacks[KEY_RUN_SERVER][KEY_BODY]:
            body += self.callbacks[KEY_RUN_SERVER][KEY_BODY]

        if self.callbacks[KEY_RUN_CLIENT][KEY_BODY]:
            body += self.callbacks[KEY_RUN_CLIENT][KEY_BODY]

        for key, access in self.callbacks[KEY_METHOD].items():
            for method in access[KEY_BODY]:
                body += method

        return Result(body)

    def generate_main(self) -> Result:
        if self.callbacks[KEY_MAIN][KEY_BODY]:
            return Result("\n" + self.callbacks[KEY_MAIN][KEY_BODY])

        return Result("")

    def generate_message_parsers(self) -> Result:
        body = ""
        for key, method in self.callbacks[KEY_PARSE].items():
            if method[KEY_BODY]:
                body += method[KEY_BODY]

            if self.callbacks[KEY_CALLBACK][key][KEY_BODY]:
                body += self.callbacks[KEY_CALLBACK][key][KEY_BODY]

        return Result(body)

    def name_from_key(self, groups):
        name = groups[0]
        args = groups[1]
        callback = groups[2]

        if callback:
            if self.is_valid_callback(callback):
                if self.callbacks[name][callback][KEY_NAME]:
                    return f'{self.callbacks[name][callback][KEY_NAME]}'
                else:
                    return f'{self.callbacks[name][callback][KEY_BODY]}'
            else:
                return  f'{self.callbacks[name][KEY_NAME]}{args}'
        else:
            if self.is_valid_callback(name):
                return f'{self.callbacks[KEY_CALLBACK][name][KEY_NAME]}{args if args else ""}'
            elif self.is_valid_key(name):
                return f'{self.callbacks[name][KEY_BODY]}{args if args else ""}'
            else:
                return f'{self.callbacks[KEY_NEW][name][KEY_BODY]}{args if args else ""}'

    def parse_language(self, parser, outer_key):
        for key in self.callbacks[outer_key]:
            if self.callbacks[outer_key][key][KEY_BODY]:
                LOG_DEBUG(f'Parsing: {outer_key}: {type(self.callbacks[outer_key][key][KEY_BODY])}')
                if isinstance(self.callbacks[outer_key][key][KEY_BODY], str):
                    self.callbacks[outer_key][key][KEY_BODY] = parser.parse(self.callbacks[outer_key][key][KEY_BODY]) + "\n"
                else:
                    for i in range(len(self.callbacks[outer_key][key][KEY_BODY])):
                        self.callbacks[outer_key][key][KEY_BODY][i] = parser.parse(self.callbacks[outer_key][key][KEY_BODY][i]) + "\n"

    def parse_dtig_language(self, parser):
        # This function should be called once the file structure is done
        self.parse_language(parser, KEY_CALLBACK)
        self.parse_language(parser, KEY_INHERIT)

        self.parse_language(parser, KEY_CONSTRUCTOR)
        self.parse_language(parser, KEY_DESTRUCTOR)
        self.parse_language(parser, KEY_MEMBER)
        self.parse_language(parser, KEY_METHOD)

    @abstractmethod
    def function_from_key(self, groups, default_name):
        raise Exception("arguments_from_key must be implemented")


