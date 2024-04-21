from tools import file_system
from common.result import *
from common.logging import *

from lexer_tokens import Location, Token, Type

class Lexer:
    def __init__(self):
        self.index = 0
        self.data = None
        self.location = Location()

        self.round = []
        self.square = []
        self.curly = []

    def ResetLocation(self):
        self.location.line += 1
        self.location.column = 1

    def Get(self):
        self.location.column += 1
        if self.index >= len(self.data):
            return None

        return self.data[self.Inc()]

    def Inc(self):
        prev = self.index
        self.index += 1
        return prev

    def Peek(self):
        if self.index >= len(self.data):
            return None

        return self.data[self.index]

    def IsIdentifierChar(self, c):
        return c.isalnum() or c == '_'

    def IsValid(self):
        if len(self.curly) > 0:
            message = f'Stray opening curly bracket{"s " if len(self.curly) > 1 else " "}'
            for token in self.curly:
                message += token.Loc() + ", "

            return VoidResult.failed(message.rstrip(", "))

        if len(self.round):
            message = f'Stray opening parenthes{"es " if len(self.round) > 1 else "is "}'
            for token in self.round:
                message += token.Loc() + ", "

            return VoidResult.failed(message.rstrip(", "))

        if len(self.square) > 0:
            message = f'Stray opening square bracket{"s " if len(self.square) > 1 else " "}'
            for token in self.square:
                message += token.Loc() + ", "

            return VoidResult.failed(message.rstrip(", "))

        return VoidResult()

    def Parse(self, filename):
        # if not file_system.exists(filename):
        #     return Result.failed(f'O arquivo {filename} não existe')

        # LOG_INFO(f'Passando pelo arquivo: {filename}')

        # with open(filename, "r") as f:
        #     self.data = f.read()
        self.data = filename

        tokens = []
        while self.index < len(self.data):
            token = self.Next()
            if token == Type.End:
                break

            # if token == Type.Unexpected:
            #     return Result.failed(f'Erro, token não reconhecido: {token.value()} at {token.Loc()}')

            tokens.append(token)

        valid = self.IsValid()
        if not valid:
            return Result.failed(f'Parse error: {valid}')

        return tokens

    def Atom(self, kind):
        self.location.column += 1
        return Token(kind, self.data[self.Inc():1], self.location)

    def Next(self):
        while self.Peek() and self.Peek().isspace():
            c = self.Peek()
            self.Get()
            if c == '\n':
                self.ResetLocation()

        c = self.Peek()
        LOG_DEBUG(f'{self.data[self.index:self.index + 4]}')
        if not c or c == '\0':
            return self.Atom(Type.End)
        elif self.data[self.index:self.index + 4] == "DTIG":
        # elif c.isalnum():
            return self.Identifier()
        # elif c.isdigit():
        #     return self.Number()
        # elif c == '<':
        #     return self.Atom(Type.LessThan)
        # elif c == '>':
        #     return self.Atom(Type.GreaterThan)
        # elif c == '=':
        #     return self.Atom(Type.Equal)
        # elif c == '+':
        #     return self.Atom(Type.Plus)
        # elif c == '-':
        #     return self.Atom(Type.Minus)
        # elif c == '*':
        #     return self.Atom(Type.Asterisk)
        # elif c == '/':
        #     return SlashOrComment()
        # elif c == '#':
        #     return self.Atom(Type.Hash)
        elif c == '.':
            return self.Atom(Type.Dot)
        # elif c == ',':
        #     return self.Atom(Type.Comma)
        # elif c == ':':
        #     return self.Atom(Type.Colon)
        # elif c == '':
        #     return self.Atom(Type.Semicolon)
        # elif c == '\'':
        #     return self.Atom(Type.SingleQuote)
        # elif c == '"':
        #     return self.Atom(Type.DoubleQuote)
        # elif c == '|':
        #     return self.Atom(Type.Pipe)
        # elif c == '&':
        #     return self.Atom(Type.And)
        else:
            return self.Bracket(c)

    def Bracket(self, c):
        if c == '(':
            token = self.Atom(Type.LeftParen)
            if token:
                 self.round.append(token)
            return token

        elif c == ')':
            token = self.Atom(Type.RightParen)
            if not len(self.round):
                return Result.failed("Stray closing parenthesis")

            self.round.pop()
            return token

        elif c == '[':
            token = self.Atom(Type.LeftSquare)
            if token:
                 self.square.append(token)
            return token

        elif c == ']':
            token = self.Atom(Type.RightSquare)
            if not len(self.square):
                return Result.failed("Stray closing square bracket")

            self.square.pop()
            return token

        elif c == '{':
            token = self.Atom(Type.LeftCurly)
            if token:
                 self.curly.append(token)

            return token

        elif c == '}':
            token = self.Atom(Type.RightCurly)
            if not len(self.curly):
                return Result.failed("Stray closing curly bracket")

            self.curly.pop()
            return token

        else:
            return self.Atom(Type.Unexpected)

    def Identifier(self):
        start = self.Inc()
        while self.IsIdentifierChar(self.Peek()):
            self.Get()

        return Token(Type.Identifier, self.data[start:self.index], self.location)

    def Number(self):
        start = self.Inc()
        while self.Peek().isdigit():
            self.Get()

        return Token(Type.Number, self.data[start:self.index-start], self.location)
