import re

from common.keys import *
from common.logging import *

from language.parser_tokens import *

from lark import Lark, Transformer, v_args

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
    ?factor: _unary_op factor | atom_expr

    arguments: test ("," test)*

    ?atom_expr: atom_expr "(" [arguments] ")" -> function_call
        | atom

    ?atom: NAME     -> var
        | NUMBER
        | "(" test ")"

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
class Evaluator(Transformer):
    from operator import add, sub, mul, truediv as div, neg

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

    def arguments(self, first, *rest):
        LOG_TRACE(f'argument: {first} {rest}')
        return first

    def function_call(self, name, args):
        LOG_TRACE(f'function_call: {name}({args})')
        if name == TOKEN_TO_PROTO_MESSAGE:
            return self.to_proto_message(args)
        elif name == TOKEN_TYPE_TO_FUNCTION:
            return self.type_to_function(args)
        elif name == TOKEN_STR:
            return self.to_string(args)
        else:
            raise Exception(f"Unknown function {name}")

    def var(self, name):
        LOG_TRACE(f'var: {name}')
        return self.get_variable(name)

    def NUMBER(self, n):
        LOG_TRACE(f'num: {n}')
        try:
            return int(n)
        except:
            raise Exception(f'Only integers are supported: {n}')

    def NAME(self, n):
        LOG_TRACE(f'name: {n}')
        return f'{n}'

    def comp_op(self, *op):
        LOG_TRACE(f'comp_op {" ".join(op)}')
        return " ".join(op)

class Parser(Evaluator):
    def __init__(self, config):
        self.cfg = config
        self.item = None
        self.item_index = 0
        self.is_copy = False

        self.index = 0
        self.contents = None
        self.else_flag = False

        self.to_string = None
        self.to_proto_message = None
        self.type_to_function = None

        self.functions = dict()

        self.lark = Lark(lark_grammar, parser='lalr', transformer=self)

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
        self.contents = text
        self.else_flag = False
        self.else_if_flag = False

        # Start from self.index 0 with no brackets
        return self.parse_ast(text)

    def parse_ast(self, contents):
        body = ""
        iter_body = contents
        while True:
            call_match = re.search(fr'{TOKEN_PREFIX}_[A-Z_]+', iter_body)
            if not call_match:
                body += iter_body
                break

            call = iter_body[call_match.start():call_match.end()]
            LOG_TRACE(f'Found: {call}')
            if call == TOKEN_IF:
                body += self.ltrim(iter_body[:call_match.start()])

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                c_and_b = []
                condition, iter_body, end = self.get_arguments(iter_body, TOKEN_IF)
                self.index += end

                # Here, we have the entire if body, from start to end
                try:
                    end, if_body, end_mode = self.get_end(iter_body, fr'\b({TOKEN_IF})\b', fr'\b({TOKEN_ELSE}|{TOKEN_ELSE_IF}|{TOKEN_END_IF})\b', TOKEN_END_IF)
                except Exception as e:
                    raise Exception(f"End of {TOKEN_IF} not found: {TOKEN_IF}({condition})")

                self.index += end
                iter_body = self.contents[self.index:]

                c_and_b.append((condition, if_body))

                while end_mode == TOKEN_ELSE_IF:
                    else_condition, iter_body, end = self.get_arguments(iter_body, TOKEN_ELSE_IF)
                    self.index += end

                    try:
                        end, else_if_body, end_mode = self.get_end(iter_body, fr'\b({TOKEN_IF})\b', fr'\b({TOKEN_ELSE}|{TOKEN_ELSE_IF}|{TOKEN_END_IF})\b', TOKEN_END_IF)
                    except Exception as e:
                        raise Exception(f"End of {TOKEN_ELSE_IF} not found: {TOKEN_IF}({condition}) ... {TOKEN_ELSE_IF}({else_condition})")

                    self.index += end
                    iter_body = self.contents[self.index:]

                    c_and_b.append((else_condition, else_if_body))

                if end_mode == TOKEN_ELSE:
                    try:
                         end, else_body, end_mode = self.get_end(iter_body, fr'\bDTIG_IF\b', fr'\bDTIG_END_IF\b', TOKEN_END_IF)
                    except Exception as e:
                        raise Exception(f"End of {TOKEN_ELSE} not found: {TOKEN_IF}({condition})...{TOKEN_ELSE}")

                    self.index += end
                    iter_body = self.contents[self.index:]

                    c_and_b.append(("True", else_body))

                for item in c_and_b:
                    if self.conditional(item[0]):
                        body += self._copy().parse(item[1])
                        break

            elif call == TOKEN_ELSE_IF:
                raise Exception(f"{TOKEN_ELSE_IF} should never be found, maybe a missing {TOKEN_ELSE_IF}")

            elif call == TOKEN_ELSE:
                raise Exception(f"{TOKEN_ELSE} should never be found, maybe a missing {TOKEN_ELSE}")

            elif call == TOKEN_END_IF:
                raise Exception(f"{TOKEN_END_IF} should never be found, maybe a missing {TOKEN_END_IF}")

            elif call == TOKEN_FOR:
                body += self.ltrim(iter_body[:call_match.start()])
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                condition, iter_body, end = self.get_arguments(iter_body, TOKEN_ELSE_IF)
                self.index += end

                try:
                    end, for_body, end_mode = self.get_end(iter_body, fr"({TOKEN_FOR})", fr"\b({TOKEN_END_FOR})\b", TOKEN_END_FOR)
                except Exception as e:
                        raise Exception(f"End of {TOKEN_FOR} not found: {TOKEN_FOR}({condition})...{TOKEN_END_FOR}")

                loop_condition = self.conditional(condition)
                if loop_condition:
                    for i, cfg in enumerate(loop_condition):
                        self.item = cfg
                        self.item_index = i

                        # Here, we have the entire if body, from start to end
                        body += self._copy().parse(for_body)

                self.index += end
                iter_body = self.contents[self.index:]

            elif call == TOKEN_END_FOR:
                raise Exception(f"{TOKEN_END_FOR} should never be found, maybe a missing {TOKEN_END_FOR}")

            elif call == TOKEN_TO_PROTO_MESSAGE:
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                cond_match = re.search(fr'\(.*?\)', iter_body)
                if not cond_match:
                    raise Exception(f'{TOKEN_TO_PROTO_MESSAGE} with no arguments')

                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                body += f'{to_replace}{self.to_proto_message(self.get_variable(condition))}'

            elif call == TOKEN_TYPE_TO_FUNCTION:
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                cond_match = re.search(fr'\(.*?\)', iter_body)
                if not cond_match:
                    raise Exception(f'{TOKEN_TYPE_TO_FUNCTION} with no arguments')

                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                var = self.get_variable(condition)
                func = self.type_to_function(var)
                body += f'{to_replace}{func}'

            elif call == TOKEN_STR:
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                condition, iter_body, end = self.get_arguments(iter_body, TOKEN_STR)
                self.index += end

                if self.to_string:
                    body += f'{to_replace}{self.to_string(self.conditional(condition))}'
                else:
                    body += f'{to_replace}{self.conditional(condition)}'

            elif call == TOKEN_DEF:
                body += self.ltrim(iter_body[:call_match.start()])
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                name_match = re.search(fr'({TOKEN_PREFIX}_[A-Z_]+)', iter_body)
                function_name = iter_body[name_match.start():name_match.end()]
                iter_body = iter_body[name_match.end():]
                self.index += name_match.end()

                function_args, iter_body, end = self.get_arguments(iter_body, TOKEN_DEF)
                self.index += end

                end, function_body, end_mode = self.get_end(iter_body, fr"({TOKEN_DEF})", fr"\b({TOKEN_END_DEF})\b", TOKEN_END_DEF)
                self.functions[function_name] = {
                    "body": function_body,
                    "args": function_args
                }

                self.index += end
                iter_body = iter_body[end:]

            elif call == TOKEN_END_DEF:
                raise Exception(f"{TOKEN_END_DEF} should never be found, maybe a missing {TOKEN_END_DEF}")

            elif call in self.functions:
                body += self.ltrim(iter_body[:call_match.start()])
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # Get the function call
                function_call = self.functions[call]

                # Replace all the arguments in the body by the found argument
                args_body, iter_body, end = self.get_arguments(iter_body, call)
                self.index += end

                args_values = [arg.strip() for arg in args_body.split(",")]
                args_names = [arg.strip() for arg in function_call["args"].split(",")]

                function_body = function_call["body"]
                for arg_value, arg_name in zip(args_values, args_names):
                    function_body = re.sub(fr'{TOKEN_PREFIX}>{arg_name}', arg_value, function_body)

                # Update iter body
                body += self._copy().parse(function_body)

            else:
                var = self.get_variable(call)
                body += f'{iter_body[:call_match.start()]}{var}'
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

        return self.ltrim(body)

    def ltrim(self, contents):
        index = 1
        for c in contents[::-1]:
            if c == "\n":
                return contents[:-index]
            elif c == " " or c == "\t":
                index += 1
            else:
                return contents

        return contents

    def get_arguments(self, contents, token):
        start = re.search(fr'\(', contents)
        index, body, end_mode = self.get_end(contents[start.end():], fr'\(', fr'\)', ")")

        # Condition, body of condition and new index
        return body, contents[start.end() + index:], index + start.end()

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

        raise Exception(f"Could not find: {end_marker}")

    def conditional(self, contents):
        return self.lark.parse(contents)

    def get_variable(self, var):
        if var == TOKEN_INDEX:
            return self.item_index
        # Item ============================
        elif var == TOKEN_ITEM_ID:
            if self.item and KEY_ID in self.item:
                return self.item[KEY_ID]
            return None
        elif var == TOKEN_ITEM_NAME:
            if self.item and KEY_NAME in self.item:
                return self.item[KEY_NAME]
            return None
        elif var == TOKEN_ITEM_TYPE:
            if self.item and KEY_TYPE in self.item:
                return self.item[KEY_TYPE]
            return None
        elif var == TOKEN_ITEM_UNIT:
            if self.item and KEY_UNIT in self.item:
                return self.item[KEY_UNIT]
            return None
        elif var == TOKEN_ITEM_NAMESPACE:
            if self.item and KEY_NAMESPACE in self.item:
                return self.item[KEY_NAMESPACE]
            return None
        elif var == TOKEN_ITEM_MODIFIER:
            if self.item and KEY_MODIFIER in self.item:
                return self.item[KEY_MODIFIER]
            return None
        elif var == TOKEN_ITEM_DESCRIPTION:
            if self.item and KEY_DESCRIPTION in self.item:
                return self.item[KEY_DESCRIPTION]
            return None
        elif var == TOKEN_ITEM_DEFAULT:
            if self.item and KEY_DEFAULT in self.item:
                return self.item[KEY_DEFAULT]
            return None
        # Inputs ==========================
        elif "INPUTS" in var:
            return self.get_from_list(var, KEY_INPUTS)
        # Outputs =========================
        elif "OUTPUTS" in var:
            return self.get_from_list(var, KEY_OUTPUTS)
        # Parameters ======================
        elif "PARAMETERS" in var:
            return self.get_from_list(var, KEY_PARAMETERS)
        # Model name ======================
        elif f"{TOKEN_PREFIX}_TYPE_" in var:
            return self.find_globals(var[5:])
        elif f"{TOKEN_PREFIX}_FORMALISM_" in var:
            return self.find_globals(var[5:])
        else:
            return self.find_globals(var)

    def get_from_list(self, var, list_name):
        if "NAMES" in var:
            if not self.cfg.has(list_name):
                return None

            return [d[KEY_NAME] for d in self.cfg[list_name] if KEY_NAME in self.cfg[list_name]]

        else:
            if not self.cfg.has(list_name):
                return None

            return self.cfg[list_name]

    def find_globals(self, call):
        # See if we are dealing with a KEY or TYPE
        if call in globals():
            return globals()[call]
        elif call.replace(f"{TOKEN_PREFIX}_", "KEY_") in globals():
            key = globals()[call.replace(f"{TOKEN_PREFIX}_", "KEY_")]
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
    from common.json_configuration import JsonConfiguration

    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/combined/fmi_config.json")

    p = Parser(config)

    from tools import cpp
    p.type_to_function = lambda variable_type: cpp.to_type(variable_type)
    p.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
    p.to_string = lambda variable_type: f'\"{variable_type}\"'

    text = """
    DTIG_DEF DTIG_READ_STRING(TYPE, NAME, INDEX)
    DTIG_IF(DTIG>INDEX == 0)
    if (item == DTIG_STR(DTIG>TYPE))
    DTIG_ELSE
    else if (item == DTIG_STR(DTIG>TYPE))
    DTIG_END_IF
    DTIG_IF(DTIG>TYPE == DTIG>NAME)
      anyValue.mutable_DTIG>TYPE()->set_value(fromData<DTIG_TYPE_TO_FUNCTION(DTIG>TYPE)>(it->second));
    DTIG_ELSE
    {
      auto val = fromData<DTIG_TYPE_TO_FUNCTION(DTIG>NAME)>(it->second);
      std::cout << "Setting input DTIG_ITEM_NAME: " << val << std::endl;
      anyValue.set_value(val);
    }
    DTIG_END_IF
    DTIG_END_DEF
    DTIG_FOR(DTIG_OUTPUTS)
    DTIG_READ_STRING(DTIG_TYPE_PROP_VALUE, DTIG_TYPE_PROP_VALUE, 0)
    DTIG_READ_STRING(DTIG_TYPE_PROP_VALUE, DTIG_TYPE_PROP_VALUE, 1)
    DTIG_END_FOR
"""

    LOG_INFO(f'{p.parse(text)}')

