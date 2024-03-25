import re

from dtig.common.logging import *
from dtig.common.result import *
from dtig.base.generator_base import GeneratorBase
from dtig.common.model_configuration_base import ModelConfigurationBase

class ServerGenerator(GeneratorBase):
  def __init__(self):
    self.callbacks = {
      "stop"       : {"name" : "stop_callback", "body" : ""},
      "start"      : {"name" : "start_callback", "body" : ""},
      "set_input"  : {"name" : "set_input_callback", "body" : ""},
      "get_output" : {"name" : "get_output_callback", "body" : ""},
      "advance"    : {"name" : "advance_callback", "body" : ""},
      "initialize" : {"name" : "initialize_callback", "body" : ""},
    }

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    return VoidResult.failed("Not implemented")

  def generate_main(self) -> str:
    return """
if __name__ == "__main__":
  wrapper = Wrapper()
  wrapper.run()
"""

  def generate_constructor(self) -> str:
    return """
  def __init__(self):
    self.state      : State  = State.UNINITIALIZED
    self.server     : socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(target=self.run_server)
    self.model_thread = threading.Thread(target=self.run_model)
"""

  def generate_imports(self, imports : str) -> str:
    return """# Basic imports
import socket
import threading

from enum import Enum
from time import sleep

# Protobuf imports
import protobuf.stop_pb2 as dti_stop
import protobuf.start_pb2 as dti_start
import protobuf.utils_pb2 as dti_utils
import protobuf.input_pb2 as dti_input
import protobuf.output_pb2 as dti_output
import protobuf.values_pb2 as dti_values
import protobuf.advance_pb2 as dti_advance
import protobuf.return_code_pb2 as dti_code
import protobuf.run_mode_pb2 as dti_run_mode
import protobuf.dt_message_pb2 as dti_message
import protobuf.return_value_pb2 as dti_return
import protobuf.initialize_pb2 as dti_initialize

from google.protobuf import any_pb2
from google.protobuf import wrappers_pb2
from google.protobuf.message import Message
from google.protobuf.message import DecodeError

#Model specific imports{0}""".format(imports)

  def generate_states(self):
    return """
HOST = "127.0.0.1"
PORT = 8080

# States utilized by the common interface
class State(Enum):
  UNINITIALIZED = 1
  INITIALIZING  = 2
  IDLE          = 3
  RUNNING       = 4
  STEPPING      = 5
  STOPPED       = 6

"""

  def generate_class(self):
    return "class Wrapper:"

  def generate_destructor(self):
    return """
  def __del__(self):
    if self.server is not None:
      self.server.close()
"""

  def generate_run(self):
    return """
  def return_code(self, code : dti_code, message : str = None) -> dti_return:
    if message is None:
      return dti_return.MReturnValue(code=code)

    return dti_return.MReturnValue(code=code, error_message=dti_utils.MString(value=message))

  def create_connection(self) -> bool:
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((HOST, PORT))
      s.listen()
      self.server = s
      print(f'Listening on {HOST}:{PORT}')
      return True

    except Exception as e:
      print(f'Failed to create socket: {e}')
      return False

  def run(self) -> None:
    if not self.create_connection():
      return

    self.server_thread.start()
    self.model_thread.start()

    self.server_thread.join()
    self.model_thread.join()

  def run_server(self) -> None:
    sock, addr = self.server.accept()
    with sock:
      print(f"{addr} connected in state {self.state.name}")
      try:
        while True:
          # Wait for client command
          data : str = sock.recv(1024)
          if not data:
            print("Client disconnected")
            break

          # Parse client command
          with self.condition:
            reply : bytes = self.parse_message(data).SerializeToString()
            sock.sendall(reply)
            self.condition.notify_all()

      except Exception as e:
        print(f'Failed: {e}')
        sock.sendall(''.encode())
        sleep(1)

      with self.condition:
        self.step = True
        self.state = State.STOPPED
        self.condition.notify_all()
"""

  def generate_run_model(self) -> str:
    return str()

  def generate_callbacks(self, file) -> Result:
    parsed_result = self._parse_callbacks_file(file)
    if not parsed_result.is_success():
      return Result.failed(f"{parsed_result}")

    generated = ""
    generated += self._generate_parse_message()
    generated += self._generate_start_callback()
    generated += self._generate_stop_callback()
    generated += self._generate_initialize_callback()
    generated += self._generate_advance_callback()
    generated += self._generate_set_input_callback()
    generated += self._generate_get_output_callback()
    return Result(generated)

  # =======================================================================
  # Private
  # =======================================================================
  def _parse_callbacks_file(self, file) -> VoidResult:
    with open(file, "r") as file:
      data = ""
      # TODO: This is not robust at all :p
      for line in file.readlines():

        l_line = len(line.lstrip())
        first_character = len(line) - l_line
        if l_line > 0 and line[first_character] == "#":
          continue

        data += "  " + line.replace("\t", "  ")

      # Get callbacks
      matches = [m for m in re.finditer('@callback\\(([a-z_]*)\\)', data)]
      for i in range(len(matches)):
        callback = matches[i]
        name = callback.groups()[0]

        if name not in self.callbacks.keys():
          return VoidResult.failed(f'Unknown callback name provided: {name}')

        start = callback.end()
        end = matches[i + 1].start() - 1 if i < len(matches) - 1 else len(data)

        LOG_INFO(f'Reading callback for {start}:{end} -> {name}')

        body = data[start:end]
        match = re.search('def.*\\((.*)\\).*:', body)
        if not match or len(match.group()) < 1:
          return VoidResult.failed(f'Could not find function header for: {name}')

        args = match.groups()[0].strip()
        if "self" not in args:
          args = "self, " + args

        # Set default callback name
        default = "def {}_callback({}):".format(name, args)
        body = body[:match.start()] + default + body[match.end():]
        if end == len(data):
          body += "\n"

        self.callbacks[name]["body"] = body

    return VoidResult()

  def _generate_parse_message(self) -> str:
    return """
  def parse_and_assign_optional(self, message, name):
    if message.HasField(name):
      return self.parse_number(getattr(message, name))

    return None

  def parse_number(self, message):
    fields = message.ListFields()
    if len(fields) != 1:
      return None

    if "proto" not in f'{type(fields[0][1])}':
      return message.value

    if message.HasField("fvalue"):
      return message.fvalue.value
    elif message.HasField("ivalue"):
      return message.ivalue.value
    elif message.HasField("uvalue"):
      return message.uvalue.value
    elif message.IsInitialized():
      return message.value

    return None

  def parse_message(self, data : str) -> Message:
    message = dti_message.MDTMessage()
    try:
      message.ParseFromString(data)
    except DecodeError as e:
      print('Failed to parse incoming message')
      return bytes()

    if message.HasField("stop"):
      return self.parse_stop(message.stop)
    elif message.HasField("start"):
      return self.parse_start(message.start)
    elif message.HasField("input"):
      return self.parse_set_input(message.input.inputs)
    elif message.HasField("output"):
      return self.parse_get_output(message.output.outputs)
    elif message.HasField("advance"):
      return self.parse_advance(message.advance)
    elif message.HasField("initialize"):
      return self.parse_initialize(message.initialize)

    return dti_return.MReturnValue(code=dti_code.UNKNOWN_COMMAND)
    """

  # =======================================================================
  # Generate the callback function called when an MStop message is received
  def _generate_stop_callback(self) -> str:
    callback = self.callbacks["stop"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  def parse_stop(self, message : dti_stop.MStop) -> Message:
    ret = self.{0}(message)
    if ret.code != dti_code.SUCCESS:
      return ret

    self.step = True
    self.state = State.STOPPED
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MStart message is received
  def _generate_start_callback(self) -> str:
    callback = self.callbacks["start"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  def parse_start(self, message : dti_start.MStart) -> Message:
    # If the model was not yet initialized, we cannot start
    if self.state == State.UNINITIALIZED:
      return dti_return.MReturnValue(
              code=dti_code.INVALID_STATE,
              error_message=dti_utils.MString(value=f'Cannot start in state {{self.state.name}}'))

    return self.{0}(message)
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MInput message is received
  def _generate_set_input_callback(self) -> str:
    callback = self.callbacks["set_input"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  def parse_set_input(self, message : dti_values.MValues) -> Message:
    # If the model was not yet initialized, we cannot set inputs
    if self.state == State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot set input in state {{self.state.name}}')

    if message.identifiers.HasField("names"):
      n_inputs = len(message.identifiers.names.names)
      for i in range(n_inputs):
        identifier : str = message.identifiers.names.names[i]
        value : any_pb2.Any = message.values[i]

        vref = self.value_references.get(identifier)
        if vref is None:
          return self.return_code(dti_code.UNKNOWN_OPTION, f'No input with id: {{identifier}}')

        fval = wrappers_pb2.FloatValue()
        if value.Unpack(fval):
          return self.{0}(identifier, fval.value)
        else:
          return self.return_code(dti_code.INVALID_OPTION, 'Non-float values not yet supported')

        if ret.code != dti_code.SUCCESS:
          return ret

    elif message.identifiers.HasField("ids"):
      n_inputs = len(message.identifiers.ids.ids)
      return self.return_code(dti_code.UNKNOWN_OPTION, 'Non-string ids not implemented')
    else:
      return self.return_code(dti_code.INVALID_OPTION, 'No identifiers provided')

    return self.return_code(dti_code.SUCCESS)
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MOutput message is received
  def _generate_get_output_callback(self) -> str:
    callback = self.callbacks["get_output"]
    return """
  def parse_get_output(self, message : dti_values.MValues) -> Message:
    if self.state == State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot get output in state {{self.state.name}}')

    if message.identifiers.HasField("names"):
      n_outputs = len(message.identifiers.names.names)
      values = self.{0}(message.identifiers.names.names)
      if len(values) != n_outputs:
        return self.return_code(dti_code.FAILURE, 'Failed to get all outputs')

      return_value = dti_return.MReturnValue(code=dti_code.SUCCESS)
      for i in range(n_outputs):
        return_value.values.identifiers.names.names.append(
          message.identifiers.names.names[i])

        # Set the output value
        value = wrappers_pb2.FloatValue()
        value.value = values[i]
        any_msg = any_pb2.Any()
        any_msg.Pack(value)
        return_value.values.values.append(any_msg)

      return return_value

    elif message.identifiers.HasField("ids"):
      n_outputs = len(message.identifiers.ids.ids)
      return self.return_code(dti_code.UNKNOWN_OPTION, 'Non-string ids not implemented')
    else:
      return self.return_code(dti_code.INVALID_OPTION, 'No identifiers provided')

    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MAdvance message is received
  def _generate_advance_callback(self) -> str:
    callback = self.callbacks["advance"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  def parse_advance(self, message : dti_advance.MAdvance) -> Message:
    if self.state != State.STEPPING:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot advance in state {{self.state.name}}')

    return self.{0}(message)
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MInitialize message is received
  def _generate_initialize_callback(self) -> str:
    callback = self.callbacks["initialize"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  def parse_initialize(self, message : dti_initialize.MInitialize) -> Message:
    if self.state != State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot initialize in state {{self.state.name}}')

    ret = self.{0}(message)
    if ret.code != dti_code.SUCCESS:
      return ret

    self.state = State.INITIALIZING
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  {1}""".format(callback["name"], callback["body"])


# =======================================================================
# Client generator
#
# Base class used to create common interface clients in python
# =======================================================================
class ClientGenerator(GeneratorBase):
  def __init__(self):
    self.callbacks = {
      "stop"       : {"name" : "stop_callback", "body" : "pass"},
      "start"      : {"name" : "start_callback", "body" : "pass"},
      "set_input"  : {"name" : "set_input_callback", "body" : "pass"},
      "get_output" : {"name" : "get_output_callback", "body" : "pass"},
      "advance"    : {"name" : "advance_callback", "body" : "pass"},
      "initialize" : {"name" : "initialize_callback", "body" : "pass"},
    }

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    return VoidResult.failed("Not implemented")

  def generate_main(self) -> str:
    return """
if __name__ == "__main__":
  wrapper = Wrapper()
  wrapper.run()
"""

  def generate_constructor(self) -> str:
    return """
  def __init__(self):
    self.state      : State  = State.UNINITIALIZED
    self.client     : socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(target=self.run_server)
    self.model_thread = threading.Thread(target=self.run_model)
"""

  def generate_imports(self, imports : str) -> str:
    return """# Basic imports
import socket
import threading

from enum import Enum
from time import sleep

# Protobuf imports
import protobuf.stop_pb2 as dti_stop
import protobuf.start_pb2 as dti_start
import protobuf.utils_pb2 as dti_utils
import protobuf.input_pb2 as dti_input
import protobuf.output_pb2 as dti_output
import protobuf.values_pb2 as dti_values
import protobuf.advance_pb2 as dti_advance
import protobuf.return_code_pb2 as dti_code
import protobuf.run_mode_pb2 as dti_run_mode
import protobuf.dt_message_pb2 as dti_message
import protobuf.return_value_pb2 as dti_return
import protobuf.initialize_pb2 as dti_initialize

from google.protobuf import any_pb2
from google.protobuf import wrappers_pb2
from google.protobuf.message import Message
from google.protobuf.message import DecodeError

#Model specific imports{0}""".format(imports)

  def generate_states(self):
    return """
HOST = "127.0.0.1"
PORT = 8080

# States utilized by the common interface
class State(Enum):
  UNINITIALIZED = 1
  INITIALIZING  = 2
  IDLE          = 3
  RUNNING       = 4
  STEPPING      = 5
  STOPPED       = 6

"""

  def generate_class(self):
    return "class Wrapper:"

  def generate_destructor(self):
    return """
  def __del__(self):
    if self.server is not None:
      self.server.close()
"""

  def generate_run(self):
    return """
  def return_code(self, code : dti_code, message : str = None) -> dti_return:
    if message is None:
      return dti_return.MReturnValue(code=code)

    return dti_return.MReturnValue(code=code, error_message=dti_utils.MString(value=message))

  def create_connection(self) -> bool:
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((HOST, PORT))
      s.listen()
      self.client = s
      print(f'Connected to {HOST}:{PORT}')
      return True

    except Exception as e:
      print(f'Failed to create socket: {e}')
      return False

  def run(self) -> None:
    if not self.create_connection():
      return

    self.server_thread.start()
    self.model_thread.start()

    self.server_thread.join()
    self.model_thread.join()

  def run_server(self) -> None:
    sock, addr = self.server.accept()
    with sock:
      print(f"{addr} connected in state {self.state.name}")
      try:
        while True:
          # Wait for client command
          data : str = sock.recv(1024)
          if not data:
            print("Client disconnected")
            break

          # Parse client command
          with self.condition:
            reply : bytes = self.parse_message(data).SerializeToString()
            sock.sendall(reply)
            self.condition.notify_all()

      except Exception as e:
        print(f'Failed: {e}')
        sock.sendall(''.encode())
        sleep(1)

      with self.condition:
        self.step = True
        self.state = State.STOPPED
        self.condition.notify_all()
"""

  def generate_run_model(self) -> str:
    return str()

  def generate_callbacks(self, file) -> Result:
    parsed_result = self._parse_callbacks_file(file)
    if not parsed_result.is_success():
      return Result.failed(f"{parsed_result}")

    generated = ""
    generated += self._generate_parse_message()
    generated += self._generate_start_callback()
    generated += self._generate_stop_callback()
    generated += self._generate_initialize_callback()
    generated += self._generate_advance_callback()
    generated += self._generate_set_input_callback()
    generated += self._generate_get_output_callback()
    return Result(generated)

  # =======================================================================
  # Private
  # =======================================================================
  def _parse_callbacks_file(self, file) -> VoidResult:
    with open(file, "r") as file:
      data = ""
      # TODO: This is not robust at all :p
      for line in file.readlines():

        l_line = len(line.lstrip())
        first_character = len(line) - l_line
        if l_line > 0 and line[first_character] == "#":
          continue

        data += "  " + line.replace("\t", "  ")

      # Get callbacks
      matches = [m for m in re.finditer('@callback\\(([a-z_]*)\\)', data)]
      for i in range(len(matches)):
        callback = matches[i]
        name = callback.groups()[0]

        if name not in self.callbacks.keys():
          return VoidResult.failed(f'Unknown callback name provided: {name}')

        start = callback.end()
        end = matches[i + 1].start() - 1 if i < len(matches) - 1 else len(data)

        LOG_INFO(f'Reading callback for {start}:{end} -> {name}')

        body = data[start:end]
        match = re.search('def.*\\((.*)\\).*:', body)
        if not match or len(match.group()) < 1:
          return VoidResult.failed(f'Could not find function header for: {name}')

        args = match.groups()[0].strip()
        if "self" not in args:
          args = "self, " + args

        # Set default callback name
        default = "def {}_callback({}):".format(name, args)
        body = body[:match.start()] + default + body[match.end():]
        if end == len(data):
          body += "\n"

        self.callbacks[name]["body"] = body

    return VoidResult()

  def _generate_parse_message(self) -> str:
    return """"""

  # =======================================================================
  # Generate the callback function called when an MStop message is received
  def _generate_stop_callback(self) -> str:
    callback = self.callbacks["stop"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MStart message is received
  def _generate_start_callback(self) -> str:
    callback = self.callbacks["start"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MInput message is received
  def _generate_set_input_callback(self) -> str:
    callback = self.callbacks["set_input"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MOutput message is received
  def _generate_get_output_callback(self) -> str:
    callback = self.callbacks["get_output"]
    return """
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MAdvance message is received
  def _generate_advance_callback(self) -> str:
    callback = self.callbacks["advance"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  {1}""".format(callback["name"], callback["body"])

  # =======================================================================
  # Generate the callback function called when an MInitialize message is received
  def _generate_initialize_callback(self) -> str:
    callback = self.callbacks["initialize"]

    # Check if the callback is defined
    if len(callback["body"]) == 0:
      return str()

    return """
  {1}""".format(callback["name"], callback["body"])