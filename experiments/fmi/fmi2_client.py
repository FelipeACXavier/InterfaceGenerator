# Basic imports
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

#Model specific imports
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np

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

class Wrapper:
  def __init__(self):
    self.state      : State  = State.UNINITIALIZED
    self.client     : socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(target=self.run_server)
    self.model_thread = threading.Thread(target=self.run_model)

  def __del__(self):
    if self.server is not None:
      self.server.close()

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

  pass
  pass
  pass
  pass
  pass
  pass
if __name__ == "__main__":
  wrapper = Wrapper()
  wrapper.run()
