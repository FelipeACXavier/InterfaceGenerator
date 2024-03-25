from enum import Enum

class Result:
  def __init__(self, data, message : str = None):
    self.data = data
    self.message = message
    self.success = self.message == None

  @staticmethod
  def failed(message):
    return Result(None, message=message)

  def is_success(self):
    return self.success

  def value(self):
    return self.data

  def __str__(self):
    return self.message

  def __add__(self, other):
    if not self.is_success():
      if not other.is_success():
        return Result.failed(f'{self} - {other}')
      else:
        return self
    elif not other.is_success():
      return other
    else:
      return Result(self.value() + other.value())

class VoidResult():
  def __init__(self, message : str = None):
    self.message = message
    self.success = self.message == None

  @staticmethod
  def failed(message):
    return VoidResult(message=message)

  def is_success(self):
    return self.success

  def __str__(self):
    return self.message
