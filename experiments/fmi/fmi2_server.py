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
    self.server     : socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(target=self.run_server)
    self.model_thread = threading.Thread(target=self.run_model)

    # Engine specific members
    self.step       : bool   = False

    self.start_time : float  = 0.0
    self.stop_time  : float  = 10.0
    self.step_size  : float  = 1e-3

    self.fmu = None
    self.model_name = None
    self.value_references = {}

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

  def run_model(self) -> None:
    with self.condition:
      self.condition.wait_for(lambda: self.state == State.INITIALIZING or self.state == State.STOPPED)
      if self.state == State.STOPPED:
        return

    print(f'Initializing FMU: {self.model_name}')

    # read the model description
    model_description = read_model_description(self.model_name)

    # collect the value references
    for variable in model_description.modelVariables:
      print(f'{variable.name} with type {variable.type}')
      self.value_references[variable.name] = variable.valueReference

    # extract the FMU
    unzipdir = extract(self.model_name)

    self.fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1')

    # initialize
    self.fmu.instantiate()
    self.fmu.setupExperiment(startTime=self.start_time)
    self.fmu.enterInitializationMode()
    self.fmu.exitInitializationMode()

    rows : list = []  # list to record the results
    time : float = self.start_time

    with self.condition:
      self.condition.wait_for(lambda: self.state == State.STEPPING or self.state == State.RUNNING or self.state == State.STOPPED)

    print(f'Running with state: {self.state.name}')
    # simulation loop
    while time < self.stop_time and self.state != State.STOPPED:
        with self.condition:
          if self.state == State.STEPPING:
            self.condition.wait_for(lambda: self.step)
            self.step = False
            print(f'Step: {time:0.4f} out of {self.stop_time:0.4f}')

        # perform one step
        self.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=self.step_size)

        # advance the time
        time += self.step_size

        outputs = self.fmu.getReal(self.value_references.values())[1:]
        rows.append((time, *outputs))

    self.fmu.terminate()
    self.fmu.freeInstance()

    if len(rows) > 0:
      # convert the results to a structured NumPy array
      result = np.array(rows, dtype=np.dtype([(k, np.float64) for k in self.value_references.keys()]))
      plot_result(result)

    with self.condition:
      if self.state != State.STOPPED:
        self.state = State.IDLE

      print(f'FMU simulation done')
      self.condition.wait_for(lambda: self.state == State.STOPPED)

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)

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
    
  def parse_start(self, message : dti_start.MStart) -> Message:
    # If the model was not yet initialized, we cannot start
    if self.state == State.UNINITIALIZED:
      return dti_return.MReturnValue(
              code=dti_code.INVALID_STATE,
              error_message=dti_utils.MString(value=f'Cannot start in state {self.state.name}'))

    return self.start_callback(message)
  
  def start_callback(self, message : dti_start.MStart):
    self.start_time = self.parse_and_assign_optional(message, "start_time")
    if self.start_time is None:
      return self.return_code(dti_code.INVALID_OPTION, f'Start time must be a float')
  
    self.stop_time = self.parse_and_assign_optional(message, "stop_time")
    if self.stop_time is None:
      return self.return_code(dti_code.INVALID_OPTION, f'Stop time must be a float')
  
    if message.HasField("step_size"):
      step_size = self.parse_number(message.step_size.step)
      if step_size is None:
        return self.return_code(dti_code.INVALID_OPTION, f'Step must be a float')
  
      self.step_size = step_size
  
    if message.run_mode == dti_run_mode.CONTINUOUS:
      self.state = State.RUNNING
    elif message.run_mode == dti_run_mode.STEP:
      self.state = State.STEPPING
    else:
      return self.return_code(dti_code.INVALID_OPTION, f'Unknown run mode: {message.run_mode}')
  
    self.step = True
    print(f'Starting with: {dti_run_mode.ERunMode.Name(message.run_mode)}.\nRunning from {self.start_time:0.4f} to {self.stop_time:0.4f} with {self.step_size:0.4f}')
  
    return dti_return.MReturnValue(code=dti_code.SUCCESS)


  def parse_stop(self, message : dti_stop.MStop) -> Message:
    ret = self.stop_callback(message)
    if ret.code != dti_code.SUCCESS:
      return ret

    self.step = True
    self.state = State.STOPPED
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  
  def stop_callback(self, message : dti_stop.MStop):
    print(f'Stopping with: {message.mode}')
    self.step = True
    self.state = State.STOPPED
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  
 
  def parse_initialize(self, message : dti_initialize.MInitialize) -> Message:
    if self.state != State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot initialize in state {self.state.name}')

    ret = self.initialize_callback(message)
    if ret.code != dti_code.SUCCESS:
      return ret

    self.state = State.INITIALIZING
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  
  def initialize_callback(self, message : dti_initialize.MInitialize):
    self.model_name = self.parse_and_assign_optional(message, "model_name")
    if self.model_name is None:
      return self.return_code(dti_code.UNKNOWN_OPTION, f'No model provided')
  
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  
 
  def parse_advance(self, message : dti_advance.MAdvance) -> Message:
    if self.state != State.STEPPING:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot advance in state {self.state.name}')

    return self.advance_callback(message)
  
  def advance_callback(self, message : dti_advance.MAdvance):
    if message.HasField("step_size"):
      step_size = self.parse_number(message.step_size.step)
      if step_size is None:
        return self.return_code(dti_code.INVALID_OPTION, f'Step must be a float')
  
      self.step_size = step_size
  
    self.step = True
    return dti_return.MReturnValue(code=dti_code.SUCCESS)
  
 
  def parse_set_input(self, message : dti_values.MValues) -> Message:
    # If the model was not yet initialized, we cannot set inputs
    if self.state == State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot set input in state {self.state.name}')

    if message.identifiers.HasField("names"):
      n_inputs = len(message.identifiers.names.names)
      for i in range(n_inputs):
        identifier : str = message.identifiers.names.names[i]
        value : any_pb2.Any = message.values[i]

        vref = self.value_references.get(identifier)
        if vref is None:
          return self.return_code(dti_code.UNKNOWN_OPTION, f'No input with id: {identifier}')

        fval = wrappers_pb2.FloatValue()
        if value.Unpack(fval):
          return self.set_input_callback(identifier, fval.value)
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
  
  def set_input_callback(self, reference, value):
    self.fmu.setReal([self.value_references[reference]], [value])
    return self.return_code(dti_code.SUCCESS)
  
 
  def parse_get_output(self, message : dti_values.MValues) -> Message:
    if self.state == State.UNINITIALIZED:
      return self.return_code(dti_code.INVALID_STATE, f'Cannot get output in state {self.state.name}')

    if message.identifiers.HasField("names"):
      n_outputs = len(message.identifiers.names.names)
      values = self.get_output_callback(message.identifiers.names.names)
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
  
  def get_output_callback(self, incoming_references):
    n_outputs = len(incoming_references)
    references = [self.value_references[ref] for ref in incoming_references]
  
    print(f'Getting values: {references}')
    values = self.fmu.getReal(references)
    print(f'Values: {values}')
  
    return values
  
 
if __name__ == "__main__":
  wrapper = Wrapper()
  wrapper.run()
