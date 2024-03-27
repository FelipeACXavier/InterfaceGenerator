import re

from abc import abstractmethod

from dtig.common.keys import *
from dtig.common.logging import *
from dtig.common.result import VoidResult
from dtig.common.model_configuration_base import ModelConfigurationBase

class TemplateItem:
  def __init__(self, name, body, is_method):
    self.name = name
    self.body = body
    self.is_method = is_method


class GeneratorBase():
    # Must be called from any children so members are initialized
    def __init__(self):
        self.config = None

        self.engine_template_file = None
        self.common_template_file = None

        self.function_regex = None
        self.function_definition = None
        self.callbacks = {
            KEY_IMPORTS         : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: False},
            KEY_RUN             : {KEY_NAME : "run",            KEY_BODY : "", KEY_SELF: False},
            KEY_MAIN            : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: False},
            KEY_STATES          : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: False},
            KEY_CLASS_NAME      : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: False},
            KEY_CONSTRUCTOR     : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: True},
            KEY_DESTRUCTOR      : {KEY_NAME : None,             KEY_BODY : "", KEY_SELF: True},
            KEY_MESSAGE_HANDLER : {KEY_NAME : "handle_message", KEY_BODY : "", KEY_SELF: True},
            KEY_RUN_SERVER      : {KEY_NAME : "run_server",     KEY_BODY : "", KEY_SELF: True},
            KEY_RUN_CLIENT      : {KEY_NAME : "run_client",     KEY_BODY : "", KEY_SELF: True},
            KEY_METHOD          : {KEY_NAME : None,             KEY_BODY : [], KEY_SELF: True},
            KEY_PARSE : {
                KEY_STOP        : {KEY_NAME : "parse_stop",       KEY_BODY : "", KEY_SELF : True},
                KEY_START       : {KEY_NAME : "parse_start",      KEY_BODY : "", KEY_SELF : True},
                KEY_SET_INPUT   : {KEY_NAME : "parse_set_input",  KEY_BODY : "", KEY_SELF : True},
                KEY_GET_OUTPUT  : {KEY_NAME : "parse_get_output", KEY_BODY : "", KEY_SELF : True},
                KEY_ADVANCE     : {KEY_NAME : "parse_advance",    KEY_BODY : "", KEY_SELF : True},
                KEY_INITIALIZE  : {KEY_NAME : "parse_initialize", KEY_BODY : "", KEY_SELF : True},
            },
            KEY_CALLBACK : {
                KEY_IMPORTS     : {KEY_NAME : None,                   KEY_BODY : "", KEY_SELF: False},
                KEY_CONSTRUCTOR : {KEY_NAME : None,                   KEY_BODY : "", KEY_SELF: False},
                KEY_DESTRUCTOR  : {KEY_NAME : None,                   KEY_BODY : "", KEY_SELF: False},
                KEY_RUN         : {KEY_NAME : "run_model",            KEY_BODY : "", KEY_SELF: False},
                KEY_STOP        : {KEY_NAME : "stop_callback",        KEY_BODY : "", KEY_SELF: True},
                KEY_START       : {KEY_NAME : "start_callback",       KEY_BODY : "", KEY_SELF: True},
                KEY_SET_INPUT   : {KEY_NAME : "set_input_callback",   KEY_BODY : "", KEY_SELF: True},
                KEY_GET_OUTPUT  : {KEY_NAME : "get_output_callback",  KEY_BODY : "", KEY_SELF: True},
                KEY_ADVANCE     : {KEY_NAME : "advance_callback",     KEY_BODY : "", KEY_SELF: True},
                KEY_INITIALIZE  : {KEY_NAME : "initialize_callback",  KEY_BODY : "", KEY_SELF: True},
            },
            }

    def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
        raise Exception("Not implemented")

    def read_templates(self) -> VoidResult:
        pass

    def parse_template(self, data, name: str, has_argument: bool = False, maximum: int = None) -> VoidResult:
        # Look for the decorators
        # Look for anything like @<name>(<args>) or @<name>
        regex = fr'^@({name}\b)(\(([a-z_]*)\))?'
        matches = [m for m in re.finditer(regex, data, flags=re.MULTILINE)]
        # Small sanity checks
        if len(matches) == 0:
            return VoidResult.failed(f'Template {name} was not defined')
        elif maximum is not None and len(matches) > maximum:
            return VoidResult.failed(f'Only {maximum} @{name} is allowed in the template')

        for match in matches:
            # Get the information from the decorator
            decorator = data[match.start():match.end()]
            decorator_name = match[1]
            decorator_arg = match[3]

            if decorator_name is None or (has_argument and decorator_arg is None):
                return VoidResult.failed(f'{decorator} a group is missing. Name {decorator_name}, Args {decorator_arg}')

            LOG_DEBUG(f'{decorator}: {decorator_name} {decorator_arg}')

            function_start = match.end() + 1
            updated_data = data[function_start:]

            # Search for the next decorator
            # @ in the middle of a function are replaced later
            end = re.search(fr'^@', updated_data, flags=re.MULTILINE)
            offset = (len(data) - len(updated_data))
            function_end = len(data) - 1 if end is None else end.end() - 1 + offset

            # Remove trailing whitespaces
            while data[function_end] == '@' or data[function_end].isspace():
                function_end -= 1

            body = data[function_start:function_end + 1]

            # Get the name of the function to be used
            callback = self.callbacks[name] if not decorator_arg else self.callbacks[name][decorator_arg]
            callback_name = callback[KEY_NAME]

            if callback[KEY_SELF]:
                definition = re.search(self.function_regex, body)
                if not definition:
                    return VoidResult.failed(f'Could not find function definition for: {name}')

                # 0 is the match as a whole, so the interesting part starts from index 1
                function_id = definition[1].strip() if callback_name is None else callback_name
                function_args = self.arguments_from_key(definition[2].strip())

                # Set default callback name
                default = self.function_definition(function_id, function_args)
                body = body[:definition.start()] + default + \
                    body[definition.end():]

            if not decorator_arg:
                if name == KEY_METHOD:
                    self.callbacks[name][KEY_BODY].append("\n" + body + "\n")
                elif name == KEY_CLASS_NAME:
                    self.callbacks[name][KEY_NAME] = body
                else:
                    self.callbacks[name][KEY_BODY] = "\n" + body + "\n"
            else:
                self.callbacks[name][decorator_arg][KEY_BODY] = "\n" + body + "\n"

        return VoidResult()

    def replace_calls(self, contents: str):
        iter_body = contents
        # Look for anything like @<name>(<args>) or @<name>
        regex = fr'@([a-z_]*\b)(\(([a-z_]*)\))?'
        while True:
            match = re.search(regex, iter_body)
            if not match:
                break

            offset = (len(contents) - len(iter_body))
            decorator = iter_body[match.start():match.end()]
            decorator_name = match[1]
            callback_name = match[3]

            replacement = self.name_from_key(decorator_name, callback_name)
            contents = contents[:match.start() + offset] + replacement + contents[match.end() + offset:]

            iter_body = iter_body[match.end():]

        return contents

    def is_valid_key(self, key):
        return key and key in self.callbacks[KEY_CALLBACK].keys()

    @abstractmethod
    def arguments_from_key(self, arguments):
        raise Exception("arguments_from_key must be implemented")

    @abstractmethod
    def name_from_key(self, name, callback):
        raise Exception("name_from_key must be implemented")


