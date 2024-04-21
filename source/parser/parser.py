import re

from common.keys import *
from common.logging import *

from lexer import Lexer
from lexer_tokens import Type

from common.json_configuration import JsonConfiguration

class Parser:
    def __init__(self, config):
        self.cfg = config
        self.item = None
        self.item_index = 0

        self.index = 0
        self.if_level = 0
        self.for_level = 0
        self.contents = ""
        self.else_flag = False

    def parse(self):
        text = """
DTIG_IF(DTIG_NOT(DTIG_INPUTS_LENGTH))
    return self.return_code(dtig_code.FAILURE, "Model has no inputs")
DTIG_ELSE
    DTIG_FOR(DTIG_INPUTS)

    DTIG_IF(DTIG_EQ(DTIG_INDEX, 0))
    if reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_ELSE
    elif reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_END_IF
        value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_NAME)

        if not any_value.Unpack(value):
            return self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {reference}")

            if not value.object:
                return self.return_code(dtig_code.FAILURE, f"No object provided: {reference}")

                # If force already exists, use that
                constraint = self.get_object(reference)
                if not constraint:
                    constraint = DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)(self.app, reference)

                obj_ref = self.app.getObject(value.object.value)
                if not obj_ref:
                    return self.return_code(dtig_code.UNKNOWN_OPTION, "Unknown output: {reference}")

                if value.reference:
                    constraint.References = [(obj_ref, value.reference.value)]
                if value.direction:
                    reverse, direction = self.direction_to_freecad(value.direction.value)
                    constraint.Direction = (direction, [""])
                    constraint.Reversed = reverse
                if value.value:
                    constraint.Force = value.value.value

                self.analysis_object.addObject(constraint)

                self.app.recompute()
                return self.return_code(dtig_code.SUCCESS)
    DTIG_END_FOR
DTIG_END_IF
        """

        self.contents = text
        LOG_INFO(self.parse_ast(text, 0, 0)) # Start from index 0 with no brackets

    def parse_ast(self, contents, c_if_level, c_for_level):
        LOG_INFO(f'Parsing: {contents}')
        body = ""
        iter_body = contents
        while True:
            call_match = re.search(fr'(DTIG_[\w\d_]+)', iter_body)
            if not call_match:
                body += iter_body
                break

            call = iter_body[call_match.start():call_match.end()]
            LOG_INFO(f'Found: {call}')
            if call == "DTIG_IF":
                # We are one level deeper now
                self.if_level += 1

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                LOG_INFO(f'Found condition: {condition}')

                # Here, we have the entire if body, from start to end
                LOG_INFO(f'Found If >>>>>>> {self.index}')
                if_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                LOG_INFO(f'Found If body: {if_body}')
                LOG_INFO(f'Found If <<<<<<< {self.index}')
                iter_body = self.contents[self.index:]

                else_body = ""
                if self.else_flag:
                    self.else_flag = False
                    LOG_INFO(f'Found Else >>>>>>> {self.index}')
                    else_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                    LOG_INFO(f'Found Else body: {else_body}')
                    LOG_INFO(f'Found Else <<<<<<< {self.index}')

                    iter_body = self.contents[self.index:]

                val = self.conditional(condition)
                if val:
                    body += if_body
                else:
                    body += else_body

            elif call == "DTIG_ELSE":
                to_replace = iter_body[:call_match.start()]
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                self.else_flag = True
                return body + to_replace

            elif call == "DTIG_END_IF":
                self.if_level -= 1

                LOG_INFO(f'Found DTIG_END_IF with {self.if_level} vs {c_if_level - 1}')
                body += iter_body[:call_match.start()]
                self.index += call_match.end()

                if self.if_level == c_if_level - 1:
                    break

                iter_body = iter_body[call_match.end():]

            elif call == "DTIG_FOR":
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                LOG_INFO(f'Found condition: {condition}')

                end_index = self.index
                prev_index = self.index
                cfg_list = self.conditional(condition)
                for i, cfg in enumerate(cfg_list):
                    self.item = cfg
                    self.item_index = i
                    self.index = prev_index

                    # We are one level deeper now, needs to be set on every iteration due to END
                    self.for_level += 1

                    # Here, we have the entire if body, from start to end
                    LOG_INFO(f'Found For >>>>>>> {self.index} - {i} of {len(cfg_list)}')
                    body += self.parse_ast(iter_body, self.if_level, self.for_level)
                    LOG_INFO(f'Found For body: {body}')
                    LOG_INFO(f'Found For <<<<<<< {self.index} vs {prev_index}')

                    if i == 0:
                        end_index = self.index

                self.index = end_index
                iter_body = self.contents[end_index:]

            elif call == "DTIG_END_FOR":
                self.for_level -= 1

                LOG_INFO(f'Found DTIG_END_FOR with {self.for_level} vs {c_for_level - 1}')
                body += iter_body[:call_match.start()]
                self.index += call_match.end()

                if self.for_level == c_for_level - 1:
                    break

                iter_body = iter_body[call_match.end():]

            elif call == "DTIG_TO_PROTO_MESSAGE":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                LOG_INFO(f'Found condition: {condition}')
                body += f'{to_replace}self.protocall({self.variable(condition)})'

            elif call == "DTIG_TYPE_TO_FUNCTION":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*?\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                LOG_INFO(f'Found condition: {condition}')
                body += f'{to_replace}self.proto_to_function({self.variable(condition)})'

            elif call == "DTIG_STR":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                LOG_INFO(f'Found condition: {condition}')
                body += f'{to_replace}\"{self.conditional(condition)}\"'

            else:
                var = self.variable(call)
                to_replace = iter_body[:call_match.start()]

                # iter_body[:call_match.end()]
                body += f'{to_replace}{var}'
                iter_body = iter_body[call_match.end():]

                self.index += call_match.end()
                LOG_INFO(f'Body: {body}')

        return body

    def conditional(self, contents):
        result = True
        iter_body = contents
        while True:
            call_match = re.search(fr'(DTIG_[\w\d_]+)', iter_body)
            if not call_match:
                return iter_body

            call = iter_body[call_match.start():call_match.end()]
            LOG_INFO(f'Found: {call}')
            regex = self.call_to_regex(call)
            cond_match = re.search(regex, iter_body)
            if not cond_match:
                return self.variable(call)

            iter_body = iter_body[call_match.end():]

            left = None
            right = None
            if len(cond_match.groups()) > 0:
                left = cond_match.groups()[0].strip(", ")
            else:
                raise Exception(f"Missing argument for {call}")

            if len(cond_match.groups()) > 1:
                right = cond_match.groups()[1].strip(", ")

            if left:
                left_side = self.conditional(left)
            if right:
                right_side = self.conditional(right)

            LOG_INFO(f"Found: {left} - {right}")
            if call == "DTIG_NOT":
                return not left_side
            elif call == "DTIG_EQ":
                return left_side == right_side
            elif call == "DTIG_AND":
                return left_side and right_side
            elif call == "DTIG_OR":
                return left_side or right_side

    def variable(self, var):
        if var == "DTIG_INDEX":
            return str(self.item_index)
        elif var == "DTIG_TRUE":
            return True
        elif var == "DTIG_FALSE":
            return False
        # Item ============================
        elif var == "DTIG_ITEM_NAME":
            return f'{self.item[KEY_NAME]}'
        elif var == "DTIG_ITEM_TYPE":
            return self.item[KEY_TYPE]
        elif var == "DTIG_ITEM_UNIT":
            return self.item[KEY_UNIT]
        elif var == "DTIG_ITEM_NAMESPACE":
            return self.item[KEY_NAMESPACE]
        elif var == "DTIG_ITEM_MODIFIER":
            return self.item[KEY_MODIFIER]
        elif var == "DTIG_ITEM_DESCRIPTION":
            return self.item[KEY_DESCRIPTION]
        # Inputs ==========================
        elif var == "DTIG_INPUTS":
            if not self.cfg.has(KEY_INPUTS) or not len(self.cfg[KEY_INPUTS]):
                return [{ "id": 0, "name": "Invalid", "type": "Invalid", "default": "Invalid", KEY_DESCRIPTION: "Invalid"},]
            return self.cfg[KEY_INPUTS]
        elif var == "DTIG_INPUTS_LENGTH":
            if self.cfg.has(KEY_INPUTS):
                return len(self.cfg[KEY_INPUTS])
            return 0
        else:
            return var

    def call_to_regex(self, call):
        if call == "DTIG_NOT":
            return fr'\((.*)\)'
        else:
            return fr'\((.*(?<=,))?(.*)\)'


if __name__ == "__main__":
    start_logger(LogLevel.TRACE)

    config = JsonConfiguration()
    config.parse("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/source/parser/config.json")

    parser = Parser(config)
    parser.parse()
