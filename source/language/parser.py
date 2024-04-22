import re

from common.keys import *
from common.logging import *

from lark import Lark, Transformer, v_args

from common.json_configuration import JsonConfiguration

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

    ?atom: NAME     -> var
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

    def __init__(self, config, variable_callback):
        self.config = config
        self.get_variable = variable_callback

    def program(self, tree):
        LOG_TRACE(f'tree: {tree}')
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

        self.index = 0
        self.if_level = 0
        self.for_level = 0
        self.contents = None
        self.else_flag = False

        self.to_proto_message = None
        self.type_to_function = None
        self.to_string = None

        self.vars = dict()

        self.lark = Lark(lark_grammar, parser='lalr', transformer=CalculateCondition(self.cfg, self.variable))

    def parse(self, text):
        # Reset all values before parsing
        self.item = None
        self.item_index = 0

        self.index = 0
        self.if_level = 0
        self.for_level = 0
        self.contents = text
        self.else_flag = False
        self.else_if_flag = False

        # Start from index 0 with no brackets
        return self.parse_ast(text, 0, 0)

    def parse_ast(self, contents, c_if_level, c_for_level):
        body = ""
        iter_body = contents
        while True:
            call_match = re.search(fr'(DTIG_[\w\d_]+)', iter_body)
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
                if_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                iter_body = self.contents[self.index:]
                c_and_b.append((condition, if_body))

                while self.else_if_flag:
                    cond_match = re.search(fr'\(.*\)', iter_body)
                    condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                    iter_body = iter_body[cond_match.end():]
                    self.index += cond_match.end()

                    self.else_if_flag = False
                    else_if_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                    iter_body = self.contents[self.index:]

                    c_and_b.append((condition, else_if_body))

                else_body = ""
                if self.else_flag:
                    self.else_flag = False
                    else_body = self.parse_ast(iter_body, self.if_level, self.for_level)
                    iter_body = self.contents[self.index:]
                    # Else is "always" true
                    c_and_b.append(("True", else_body))

                for item in c_and_b:
                    if self.conditional(item[0]):
                        body += item[1].rstrip()
                        break

            elif call == "DTIG_ELSE_IF":
                body += iter_body[:call_match.start()].rstrip()
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                self.else_if_flag = True
                return body

            elif call == "DTIG_ELSE":
                body += iter_body[:call_match.start()].rstrip()
                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                self.else_flag = True
                return body

            elif call == "DTIG_END_IF":
                self.if_level -= 1

                body += iter_body[:call_match.start()].rstrip()
                self.index += call_match.end()

                if self.if_level == c_if_level - 1:
                    break

                iter_body = iter_body[call_match.end():]

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

                body += f'{to_replace}{self.type_to_function(self.variable(condition))}'

            elif call == "DTIG_STR":
                to_replace = iter_body[:call_match.start()]

                iter_body = iter_body[call_match.end():]
                self.index += call_match.end()

                # TODO: Check for success
                cond_match = re.search(fr'\(.*?\)', iter_body)
                condition = iter_body[cond_match.start() + 1:cond_match.end() - 1]

                iter_body = iter_body[cond_match.end():]
                self.index += cond_match.end()

                body += f'{to_replace}{self.to_string(self.conditional(condition))}'

            else:
                var = self.variable(call)
                to_replace = iter_body[:call_match.start()]

                body += f'{to_replace}{var}'
                iter_body = iter_body[call_match.end():]

                self.index += call_match.end()

        return body

    def conditional(self, contents):
        result = True
        iter_body = contents
        ret = self.lark.parse(contents)
        return ret

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
        # Variables =======================
        else:
            return self.type_to_regex(var)

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

    def type_to_regex(self, call):
        if call == "TYPE_BOOL":
            return TYPE_BOOL
        elif call == "TYPE_BYTES":
            return TYPE_BYTES
        elif call == "TYPE_STRING":
            return TYPE_STRING
        elif call == "TYPE_INT_8":
            return TYPE_INT_8
        elif call == "TYPE_INT_16":
            return TYPE_INT_16
        elif call == "TYPE_INT_32":
            return TYPE_INT_32
        elif call == "TYPE_INT_64":
            return TYPE_INT_64
        elif call == "TYPE_UINT_8":
            return TYPE_UINT_8
        elif call == "TYPE_UINT_16":
            return TYPE_UINT_16
        elif call == "TYPE_UINT_32":
            return TYPE_UINT_32
        elif call == "TYPE_UINT_64":
            return TYPE_UINT_64
        elif call == "TYPE_FLOAT_32":
            return TYPE_FLOAT_32
        elif call == "TYPE_FLOAT_64":
            return TYPE_FLOAT_64
        elif call == "TYPE_FORCE":
            return TYPE_FORCE
        elif call == "TYPE_FIXTURE":
            return TYPE_FIXTURE
        elif call == "TYPE_MESH":
            return TYPE_MESH
        elif call == "TYPE_SOLID":
            return TYPE_SOLID
        else:
            return self.key_to_regex(call)

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
    config.parse("/media/felaze/NotAnExternalDrive/TUe/Graduation/code/InterfaceGenerator/experiments/freecad/config.json")

    p = Parser(config)

    text = """
def get_model_info(references):
    if not self.model_name:
        return self.return_code(dtig_code.FAILURE, f'Model is not yet known')

    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    DTIG_FOR(DTIG_INPUTS)
    info_DTIG_ITEM_NAME = dtig_info.MInfo()

    DTIG_IF(4 < 1)
    info_DTIG_ITEM_NAME.id.value = 1
    DTIG_ELSE_IF(4 < 2)
    info_DTIG_ITEM_NAME.id.value = 2
    DTIG_ELSE_IF(4 < 3)
    info_DTIG_ITEM_NAME.id.value = 3
    DTIG_ELSE_IF(4 < 4)
    info_DTIG_ITEM_NAME.id.value = 4
    DTIG_ELSE_IF(6 < 5)
    info_DTIG_ITEM_NAME.id.value = 5
    DTIG_ELSE
    info_DTIG_ITEM_NAME.id.value = 6
    DTIG_END_IF

    return_value.model_info.inputs.append(info_DTIG_ITEM_NAME)
    DTIG_END_FOR

    return return_value
    """
    LOG_INFO(p.parse(text))