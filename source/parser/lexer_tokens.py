from enum import Enum
from dataclasses import dataclass

@dataclass
class Location:
    def __init__(self):
        self.line = 0
        self.column = 0

class Type(Enum):
  Number        = 0,
  Identifier    = 1,
  LeftParen     = 2,
  RightParen    = 3,
  LeftSquare    = 4,
  RightSquare   = 5,
  LeftCurly     = 6,
  RightCurly    = 7,
  LessThan      = 8,
  GreaterThan   = 9,
  Equal         = 10,
  Plus          = 11,
  Minus         = 12,
  Asterisk      = 13,
  Slash         = 14,
  Hash          = 15,
  Dot           = 16,
  Comma         = 17,
  Colon         = 18,
  Semicolon     = 19,
  SingleQuote   = 20,
  DoubleQuote   = 21,
  Comment       = 22,
  Pipe          = 23,
  And           = 24,
  End           = 25,
  Unexpected    = 26,

class Token:
    def __init__(self, kind, value = None, loc = None):
        self._id = kind
        self._value = value

        self._loc = Location()
        self._loc.line = loc.line
        self._loc.column = loc.column

    def id(self):
        return self._id

    def value(self):
        return self._value

    def Loc(self):
        if not self._loc:
            return f''

        return f'{self._loc.line}:{self._loc.column}'

    def IsOneOf(self, ones):
        return self.id() in ones

    def __eq__(self, other):
        return self.id() == other

    def __ne__(self, other):
        return self.id() == other

    def __str__(self):
        return f'{self.id()}:({self.Loc()}) {self.value()}'

    def __repr__(self):
        return self.__str__()

    def __format__(self, spec):
        return self.__str__()