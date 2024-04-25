import re

from common.keys import *
from common.logging import *
from common.json_configuration import JsonConfiguration

from lark import Lark, Transformer, v_args

# TODO: How to improve this? For now we need to go through the for loop at least once
class default_list(list):
    def __init__(self):
        super().__init__()
        super().append({
            KEY_ID: 0,
            KEY_DESCRIPTION: "Invalid",
            KEY_TYPE: "Invalid",
            KEY_DEFAULT: "Invalid",
            KEY_DESCRIPTION: "Invalid"
        })

    def __bool__(self):
        return False

lark_grammar= r"""
    ?start: test    -> program

    ?test: or_test
    ?or_test: and_test ("OR" and_test)*
    ?and_test: not_test_ ("AND" not_test_)*
    ?not_test_: "NOT" not_test_ -> not_test
        | "HAS" not_test_ -> has_test
        | comparison

    ?comparison: expr (comp_op expr)*

    ?expr: arith_expr
    ?arith_expr: term (_add_op term)*
    ?term: factor (_mul_op factor)*
    ?factor: _unary_op factor | atom

    ?argument: test ("," argument)*
    ?function_call: NAME "(" argument ")"

    ?atom: function_call
        | NAME     -> var
        | NUMBER
        | "(" test ")"
        | "NONE"    -> const_none
        | "DTIG_TRUE"    -> const_true
        | "DTIG_FALSE"   -> const_false

    !_unary_op: "+"|"-"
    !_add_op: "+"|"-"
    !_mul_op: "*"|"/"|"%"

    !comp_op: "<"|">"|"=="|">="|"<="|"!="|"IN"|"NOT" "IN"|"IS"|"IS" "NOT"

    %import common.CNAME                -> NAME
    %import common.SIGNED_NUMBER        -> NUMBER
    %import common.NEWLINE
    %import common.WS
    %ignore WS
    %ignore NEWLINE
"""

@v_args(inline=True)    # Affects the signatures of the methods
class CalculateCondition(Transformer):
    from operator import add, sub, mul, truediv as div, neg
    number = float

    def __init__(self, config, variable_callback, to_proto_message, type_to_function):
        self.config = config
        self.get_variable = variable_callback
        self.to_proto_message = to_proto_message
        self.type_to_function = type_to_function

    def program(self, tree):
        return tree

    def or_test(self, left, right):
        LOG_TRACE(f'{left} or {right}')
        return left or right

    def and_test(self, left, right):
        LOG_TRACE(f'{left} and {right}')
        return left and right

    def not_test(self, left):
        LOG_TRACE(f'not {left}')
        return not left

    def has_test(self, left):
        LOG_TRACE(f'has {left}')
        return left is not None

    def comparison(self, left, op, right):
        LOG_TRACE(f'{left} {op} {right}')
        if op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "==":
            return left == right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right
        elif op == "!=":
            return left != right
        elif op == "IN":
            return left in right
        elif op == "NOT IN":
            return left not in right
        elif op == "IS":
            return left is right
        elif op == "IS NOT":
            return left is not right
        else:
            raise Exception(f"Unknown operator: {op}")

    def arith_expr(self, left, op, right):
        LOG_TRACE(f'{left} {op} {right}')
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left / right
        elif op == "%":
            return left % right
        else:
            raise Exception(f"Unknown arithmetic operator: {op}")

    def argument(self, first, rest):
        LOG_TRACE(f'argument: {first}, {rest}')
        pass

    def function_call(self, name, args):
        LOG_TRACE(f'function_call: {name}({args})')
        if name == "DTIG_TO_PROTO_MESSAGE":
            return self.to_proto_message(args)
        elif name == "DTIG_TYPE_TO_FUNCTION":
            return self.type_to_function(args)

    def var(self, name):
        LOG_TRACE(f'var: {name}')
        return self.get_variable(name)

    def NUMBER(self, n):
        LOG_TRACE(f'num: {n}')
        try:
            return int(n)
        except:
            raise Exception(f'Only integers are supported: {n}')

    def comp_op(self, *op):
        LOG_TRACE(f'comp_op {" ".join(op)}')
        return " ".join(op)

    def const_true(self):
        return True

    def const_false(self):
        return False

class Parser:
    def __init__(self, config):
        self.cfg = config
        self.item = None
        self.item_index = 0
        self.is_copy = False

        self.index = 0
        self.if_level = 0
        self.for_level = 0
        self.contents = None
        self.else_flag = False

        self.to_string = None
        self.to_proto_message = None
        self.type_to_function = None

        self.functions = dict()

        self.lark = Lark(lark_grammar, parser='lalr',
            transformer=CalculateCondition(self.cfg, self.variable, lambda x : self.to_proto_message(x), lambda x: self.type_to_function(x)))

    def _copy(self):
        parser = Parser(self.cfg)
        parser.is_copy = True
        parser.item = self.item
        parser.item_index = self.item_index

        parser.functions = self.functions

        parser.to_string = self.to_string
        parser.to_proto_message = self.to_proto_message
        parser.type_to_function = self.type_to_function

        return parser

    def parse(self, text):
        # Reset all values before parsing
        if not self.is_copy:
            self.item = None
            self.item_index = 0

        self.index = 0
        self.if_level = 0
        self.for_level = 0
        self.contents = text
        self.else_flag = False
        self.else_if_flag = False

        # Start from self.index 0 with no brackets
        return self.parse_ast(text, 0, 0)

    def parse_ast(self, contents, c_if_level, c_for_level):
        body = ""
        iter_body = contents
        while True:
            call_match = re.search(fr'DTIG_[A-Z_]+', iter_body)
            if not call_match:
                body += iter_body.rstrip()
                break

            call = iter_body[call_match.start():call_match.end()]
            LOG_TRACE(f'Found: {call}')
            if call == "DTIG_IF":
                body += iter_body[:call_match.start()].rstrip()
                # We are one level deeper now
                self.if_level += 1

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                c_and_b = []
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                # Here, we have the entire if body, from start to end
                try:
                    end, if_body, end_mode = self.get_end(iter_body, fr'\bDTIG_IF\b', fr'\b(DTIG_ELSE|DTIG_ELSE_IF|DTIG_END_IF)\b', "DTIG_END_IF")
                except Exception as e:
                    raise Exception(f"End of DTIG_IF not found: DTIG_IF({condition})")

                self.index += end
                iter_body = self.contents[self.index:]

                c_and_b.append((condition, if_body))

                while end_mode == "DTIG_ELSE_IF":
                    cond_match = re.search(fr'\(.*\)', iter_body)
                    else_condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                    iter_body = iter_body[cond_match.end():]
                    self.index += cond_match.end()
                    try:
                        end, else_if_body, end_mode = self.get_end(iter_body, fr'\bDTIG_IF\b', fr'\b(DTIG_ELSE|DTIG_ELSE_IF|DTIG_END_IF)\b', "DTIG_END_IF")
                    except Exception as e:
                        raise Exception(f"End of DTIG_ELSE_IF not found: DTIG_IF({condition}) ... DTIG_ELSE_IF({else_condition})")

                    self.index += end
                    iter_body = self.contents[self.index:]

                    c_and_b.append((else_condition, else_if_body))

                if end_mode == "DTIG_ELSE":
                    try:
                        end, else_body, end_mode = self.get_end(iter_body, fr'\bDTIG_IF\b', fr'\bDTIG_END_IF\b', "DTIG_END_IF")
                    except Exception as e:
                        raise Exception(f"End of DTIG_ELSE not found: DTIG_IF({condition})...DTIG_ELSE")

                    self.index += end
                    iter_body = self.contents[self.index:]

                    c_and_b.append(("True", else_body))

                for item in c_and_b:
                    if self.conditional(item[0]):
                        body += self._copy().parse(item[1])
                        break

            elif call == "DTIG_ELSE_IF":
                raise Exception("DTIG_ELSE_IF should never be found, maybe a missing DTIG_ELSE_IF")

            elif call == "DTIG_ELSE":
                raise Exception("DTIG_ELSE should never be found, maybe a missing DTIG_ELSE")

            elif call == "DTIG_END_IF":
                raise Exception("DTIG_END_IF should never be found, maybe a missing DTIG_END_IF")

            elif call == "DTIG_FOR":
                body += iter_body[:call_match.start()].rstrip()
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                end_index = self.index
                prev_index = self.index
                cfg_list = self.conditional(condition)
                is_default = cfg_list == default_list()
                for i, cfg in enumerate(cfg_list):
                    self.item = cfg
                    self.item_index = i
                    self.index = prev_index

                    # We are one level deeper now, needs to be set on every iteration due to END
                    self.for_level += 1

                    # Here, we have the entire if body, from start to end
                    tmp_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                    if not is_default:
                        body += tmp_body

                    if i == 0:
                        end_index = self.index

                self.index = end_index
                iter_body = self.contents[end_index:]

            elif call == "DTIG_END_FOR":
                self.for_level -= 1

                body += iter_body[:call_match.start()].rstrip()
                self.index += call_match.end()

                if self.for_level == c_for_level - 1:
                    break

                iter_body = iter_body[call_match.end():]

            elif call == "DTIG_TO_PROTO_MESSAGE":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*?\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                body += f'{to_replace}{self.to_proto_message(self.variable(condition))}'

            elif call == "DTIG_TYPE_TO_FUNCTION":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*?\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                var = self.variable(condition)
                func = self.type_to_function(var)
                body += f'{to_replace}{func}'

            elif call == "DTIG_STR":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*?\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                if self.to_string:
                    body += f'{to_replace}{self.to_string(self.conditional(condition))}'
                else:
                    body += f'{to_replace}{self.conditional(condition)}'

            elif call == "DTIG_DEF":
                body += iter_body[:call_match.start()].rstrip()
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                name_match = re.search(fr'(DTIG_[A-Z_]+)', iter_body)
                function_name = iter_body[name_match.start():name_match.end()]
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                args_match = re.search(fr'\(.*\)', iter_body)
                function_args = iter_body[args_match.start() + 1:args_match.end() - 1]
                iter_body = iter_body[args_match.end():]
                self.index += args_match.end()

                function_end = re.search(fr'DTIG_END_DEF', iter_body)
                function_body = iter_body[:function_end.start()].rstrip()

                self.functions[function_name] = {
                    "body": function_body,
                    "args": function_args
                }

                iter_body = iter_body[function_end.end():]
                self.index += function_end.end()

            elif call == "DTIG_END_DEF":
                raise Exception("DTIG_END_DEF should never be found, maybe a missing DTIG_END_DEF")

            elif call in self.functions:
                body += iter_body[:call_match.start()].rstrip()
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # Get the function call
                function_call = self.functions[call]

                # Replace all the arguments in the body by the found argument
                args_match = re.search(fr'\(.*\)', iter_body)
                args_body = iter_body[args_match.start() + 1:args_match.end() - 1]
                args_values = [arg.strip() for arg in args_body.split(",")]
                args_names = [arg.strip() for arg in function_call["args"].split(",")]

                function_body = function_call["body"]
                for arg_value, arg_name in zip(args_values, args_names):
                    function_body = re.sub(fr'DTIG>{arg_name}', arg_value, function_body)

                # Update iter body
                iter_body = iter_body[args_match.end():]
                self.index += args_match.end()

                parser = self._copy()
                ret_body = parser.parse(function_body)

                body += ret_body

            else:
                var = self.variable(call)
                to_replace = iter_body[:call_match.start()]

                body += f'{to_replace}{var}'
                iter_body = iter_body[call_match.end():]

                self.index += call_match.end()

        return body

    def get_end(self, contents, start_regex, end_regex, end_marker):
        index = 0
        iter_body = contents
        level = 0
        while iter_body:
            a = re.search(start_regex, iter_body)
            b = re.search(end_regex, iter_body)

            if not b:
                break

            # If nesting, continue
            if a and a.start() < b.start():
                level += 1
                index += a.end()
                iter_body = iter_body[a.end():]
                continue

            end_mode = iter_body[b.start():b.end()]
            if level == 0:
                return index + b.end(), contents[0:index + b.start()], end_mode

            if end_mode == end_marker:
                level -= 1

            index += b.end()
            iter_body = iter_body[b.end():]

        raise Exception()

    def conditional(self, contents):
        return self.lark.parse(contents)

    def variable(self, var):
        if var == "DTIG_INDEX":
            return self.item_index
        elif var == "DTIG_TRUE":
            return True
        elif var == "DTIG_FALSE":
            return False
        # Item ============================
        elif var == "DTIG_ITEM":
            return self.item
        elif var == "DTIG_ITEM_ID":
            if self.item and KEY_ID in self.item:
                return self.item[KEY_ID]
            return None
        elif var == "DTIG_ITEM_NAME":
            if self.item and KEY_NAME in self.item:
                return self.item[KEY_NAME]
            return None
        elif var == "DTIG_ITEM_TYPE":
            if self.item and KEY_TYPE in self.item:
                return self.item[KEY_TYPE]
            return None
        elif var == "DTIG_ITEM_UNIT":
            if self.item and KEY_UNIT in self.item:
                return self.item[KEY_UNIT]
            return None
        elif var == "DTIG_ITEM_NAMESPACE":
            if self.item and KEY_NAMESPACE in self.item:
                return self.item[KEY_NAMESPACE]
            return None
        elif var == "DTIG_ITEM_MODIFIER":
            if self.item and KEY_MODIFIER in self.item:
                return self.item[KEY_MODIFIER]
            return None
        elif var == "DTIG_ITEM_DESCRIPTION":
            if self.item and KEY_DESCRIPTION in self.item:
                return self.item[KEY_DESCRIPTION]
            return None
        elif var == "DTIG_ITEM_DEFAULT":
            if self.item and KEY_DEFAULT in self.item:
                return self.item[KEY_DEFAULT]
            return None
        # Inputs ==========================
        elif "INPUTS" in var:
            return self.get_from_list(var, "INPUTS", KEY_INPUTS)
        # Outputs =========================
        elif "OUTPUTS" in var:
            return self.get_from_list(var, "OUTPUTS", KEY_OUTPUTS)
        # Parameters ======================
        elif "PARAMETERS" in var:
            return self.get_from_list(var, "PARAMETERS", KEY_PARAMETERS)
        elif var == "DTIG_ALL":
            all_values = []
            if self.cfg.has(KEY_INPUTS):
                all_values += self.cfg[KEY_INPUTS]
            if self.cfg.has(KEY_OUTPUTS):
                all_values += self.cfg[KEY_OUTPUTS]
            if self.cfg.has(KEY_PARAMETERS):
                all_values += self.cfg[KEY_PARAMETERS]

            if not len(all_values):
                return default_list()

            return all_values
        # Variables =======================
        # Model name ======================
        elif "DTIG_TYPE_" in var:
            return self.find_globals(var[5:])
        elif "DTIG_FORMALISM_" in var:
            return self.find_globals(var[5:])
        else:
            return self.find_globals(var)

    def get_from_list(self, var, name, key_name):
        if var == f'DTIG_{name}':
            if not self.cfg.has(key_name) or not len(self.cfg[key_name]):
                return default_list()
            return self.cfg[key_name]

        elif var == f"DTIG_{name}_LENGTH":
            if self.cfg.has(key_name):
                return len(self.cfg[key_name])
            return 0

        elif var == f"DTIG_{name}_NAMES":
            if not self.cfg.has(key_name):
                return None
            names = []
            for item in self.cfg[key_name]:
                if KEY_NAME in item:
                    names.append(item[KEY_NAME])
            return names

        elif var == f"DTIG_{name}_IDS":
            if not self.cfg.has(key_name):
                return None
            names = []
            for item in self.cfg[key_name]:
                if KEY_ID in item:
                    names.append(item[KEY_ID])
            return names

    def find_globals(self, call):
        # See if we are dealing with a KEY or TYPE
        if call in globals():
            return globals()[call]
        elif call.replace("DTIG_", "KEY_") in globals():
            key = globals()[call.replace("DTIG_", "KEY_")]
            if not self.cfg.has(key):
                return None

            return self.cfg[key]
        else:
            return call

    def key_to_regex(self, call):
        if call == "KEY_ID":
            return KEY_ID
        elif call == "KEY_NAME":
            return KEY_NAME
        elif call == "KEY_TYPE":
            return KEY_TYPE
        elif call == "KEY_UNIT":
            return KEY_UNIT
        elif call == "KEY_DEFAULT":
            return KEY_DEFAULT
        elif call == "KEY_MODIFIER":
            return KEY_MODIFIER
        elif call == "KEY_NAMESPACE":
            return KEY_NAMESPACE
        elif call == "KEY_DESCRIPTION":
            return KEY_DESCRIPTION
        else:
            return call

if __name__ == "__main__":
    start_logger(LogLevel.TRACE)
    config = JsonConfiguration()
    config.parse("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/combined/fmi_config.json")

    p = Parser(config)

    from tools import cpp
    p.type_to_function = lambda variable_type: cpp.to_type(variable_type)
    p.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
    p.to_string = lambda variable_type: f'\"{variable_type}\"'

    text = """
def get_parameter(self, sock):
    message = dtig_message.MDTMessage()
    DTIG_FOR(DTIG_PARAMETERS)
        message.get_parameter.parameters.identifiers.append(DTIG_STR(DTIG_ITEM_NAME))
    DTIG_END_FOR

    def handler(response):
        if response.HasField("values"):
            for i in range(len(response.values.values)):
                param = response.values.identifiers[i]
                any_value = response.values.values[i]
                DTIG_FOR(DTIG_PARAMETERS)
                DTIG_IF(DTIG_INDEX == 0)
                if param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_ELSE
                elif param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_END_IF
                    value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
                    if any_value.Unpack(value):
                        LOG_INFO(f'DTIG_ITEM_NAME: {value.value}')
                DTIG_END_FOR

    self.send_message(sock, message, handler)
    """
    LOG_INFO(p.parse(text))
