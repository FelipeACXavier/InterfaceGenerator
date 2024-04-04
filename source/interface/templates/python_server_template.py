# @imports
# Basic imports
import sys
import socket
import threading

from enum import Enum
from time import sleep

# Protobuf imports
import dtig.stop_pb2 as dtig_stop
import dtig.info_pb2 as dtig_info
import dtig.start_pb2 as dtig_start
import dtig.utils_pb2 as dtig_utils
import dtig.input_pb2 as dtig_input
import dtig.output_pb2 as dtig_output
import dtig.values_pb2 as dtig_values
import dtig.advance_pb2 as dtig_advance
import dtig.return_code_pb2 as dtig_code
import dtig.run_mode_pb2 as dtig_run_mode
import dtig.dt_message_pb2 as dtig_message
import dtig.return_value_pb2 as dtig_return
import dtig.model_info_pb2 as dtig_model_info
import dtig.initialize_pb2 as dtig_initialize

from google.protobuf import any_pb2
from google.protobuf.message import Message
from google.protobuf.message import DecodeError

# @classname
FMI2Wrapper

# @constructor(public)
def __init__(self):
    self.state: State = State.UNINITIALIZED
    self.server: socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(
        target=#@>callback(runserver)
    )
    self.model_thread = threading.Thread(
        target=#@>callback(runmodel)
    )

# @destructor(public)
def __del__(self):
    if self.server is not None:
        self.server.close()

# @run
def run(self) -> None:
    if not self.create_connection():
        return

    self.server_thread.start()
    self.model_thread.start()

    self.server_thread.join()
    self.model_thread.join()

# @parse(initialize)
def parse_initialize(message) -> Message:
    if self.state != State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot initialize in state {self.state.name}')

    ret = # @>callback(initialize)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.state = State.INITIALIZING
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @parse(start)
def parse_start(message) -> Message:
    # If the model was not yet initialized, we cannot start
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot start in state {self.state.name}')

    return # @>callback(start)(message)

# @parse(stop)
def parse_stop(message) -> Message:
    ret = # @>callback(stop)(message)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.step = True
    self.state = State.STOPPED
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @parse(set_input)
def parse_set_input(message) -> Message:
    # If the model was not yet initialized, we cannot set inputs
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot set input in state {self.state.name}')

    ids_length = len(message.inputs.identifiers)
    for i in range(ids_length):
        identifier : str = message.inputs.identifiers[i]
        any_value : any_pb2.Any = message.inputs.values[i]

        # Only the model knows the type, unpacking must be a responsibility of the callback function
        ret = # @>callback(set_input)(identifier, any_value)
        if ret.code != dtig_code.SUCCESS:
            return ret

    return self.return_code(dtig_code.SUCCESS)

# @parse(get_output)
def parse_get_output(message) -> dtig_return.MReturnValue:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get output in state {self.state.name}')

    ids_length = len(message.outputs.identifiers)
    return_message = # @>callback(get_output)(message.outputs.identifiers)
    if len(return_message.values.identifiers) != ids_length and return_message.code != dtig_code.SUCCESS:
        return_message.code = dtig_code.FAILURE
        return_message.error_message = 'Failed to get all outputs'

    return return_message

# @parse(set_parameter)
def parse_set_parameter(message) -> dtig_return.MReturnValue:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot set parameter in state {self.state.name}')

    ids_length = len(message.parameters.identifiers)
    for i in range(ids_length):
        identifier : str = message.parameters.identifiers[i]
        any_value : any_pb2.Any = message.parameters.values[i]

        # Only the model knows the type, unpacking must be a responsibility of the callback function
        ret = # @>callback(set_parameter)(identifier, any_value)
        if ret.code != dtig_code.SUCCESS:
            return ret

    return self.return_code(dtig_code.SUCCESS)

# @parse(get_parameter)
def parse_get_parameter(message) -> dtig_return.MReturnValue:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get parameter in state {self.state.name}')

    ids_length = len(message.parameters.identifiers)
    return_message = # @>callback(get_parameter)(message.parameters.identifiers)
    if len(return_message.values.identifiers) != ids_length and return_message.code != dtig_code.SUCCESS:
        return_message.code = dtig_code.FAILURE
        return_message.error_message = 'Failed to get all outputs'

    return return_message

# @parse(advance)
def parse_advance(message) -> Message:
    if self.state != State.STEPPING:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot advance in state {self.state.name}')

    return # @>callback(advance)(message)

# @parse(initialize)
def parse_initialize(message) -> Message:
    if self.state != State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot initialize in state {self.state.name}')

    ret = # @>callback(initialize)(message)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.state = State.INITIALIZING
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @parse(model_info)
def parse_model_info() -> Message:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get model info in state {self.state.name}')

    return # @>callback(model_info)()

# @messagehandler
def parse_message(self, data : str) -> Message:
    message = dtig_message.MDTMessage()
    try:
        message.ParseFromString(data)
    except DecodeError as e:
        print('Failed to parse incoming message')
        return bytes()

    if message.HasField("advance"):
        return # @>parse(advance)(message.advance)
    elif message.HasField("set_input"):
        return # @>parse(set_input)(message.set_input)
    elif message.HasField("get_output"):
        return # @>parse(get_output)(message.get_output)
    elif message.HasField("initialize"):
        return # @>parse(initialize)(message.initialize)
    elif message.HasField("start"):
        return # @>parse(start)(message.start)
    elif message.HasField("stop"):
        return # @>parse(stop)(message.stop)
    elif message.HasField("set_parameter"):
        return # @>parse(set_parameter)(message.set_parameter)
    elif message.HasField("get_parameter"):
        return # @>parse(get_parameter)(message.get_parameter)
    else:
        return # @>parse(model_info)()

    return dtig_return.MReturnValue(code=dtig_code.UNKNOWN_COMMAND)

# @method(public)
def return_code(self, code: dtig_code, message: str = None) -> dtig_return:
    if message is None:
        return dtig_return.MReturnValue(code=code)

    return dtig_return.MReturnValue(code=code, error_message=dtig_utils.MString(value=message))

# @method(public)
def create_connection(self) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        self.server = s
        print(f'Connected to {HOST}:{PORT}')
        return True

    except Exception as e:
        print(f'Failed to create socket: {e}')
        return False

# @runserver
def run_server(self) -> None:
    sock, addr = self.server.accept()
    with sock:
        print(f"{addr} connected in state {self.state.name}")
        try:
            while True:
                # Wait for client command
                data: str = sock.recv(1024)
                if not data:
                    print("Client disconnected")
                    break

                # Parse client command
                with self.condition:
                    reply: bytes = # @>messagehandler(data).SerializeToString()
                    # Is this always desired
                    # On step, we wait until the step is complete before replying
                    if not self.step:
                        sock.sendall(reply)
                        self.condition.notify_all()
                    else:
                        self.condition.notify_all()
                        self.condition.wait_for(lambda: not self.step or self.state == State.STOPPED)
                        sock.sendall(reply)

                    if self.state == State.STOPPED:
                        break

        except Exception as e:
            print(f'Failed: {e}')
            sock.sendall(''.encode())
            sleep(1)

        with self.condition:
            self.step = True
            self.state = State.STOPPED
            self.condition.notify_all()

# @main
if __name__ == "__main__":
    print(sys.argv)
    for i, arg in enumerate(sys.argv):
        if arg == "--host":
            HOST = sys.argv[i + 1]
        elif arg == "--port":
            PORT = int(sys.argv[i + 1])

    wrapper = # @>classname()
    wrapper.# @>run()

# @states
HOST = "127.0.0.1"
PORT = 8080

class State(Enum):
    UNINITIALIZED = 1
    INITIALIZING = 2
    IDLE = 3
    RUNNING = 4
    STEPPING = 5
    STOPPED = 6

# @callback(initialize)
def initialize_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support initialize call')

# @callback(advance)
def advance_callback(self, message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support advance call')

# @callback(stop)
def stop_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support stop call')

# @callback(start)
def start_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support start call')

# @callback(model_info)
def model_info_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support model_info call')

# @callback(set_input)
def set_input_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support set_input call')

# @callback(get_output)
def get_output_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support get_output call')

# @callback(set_parameter)
def set_parameter_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support set_parameter call')

# @callback(get_parameter)
def get_parameter_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support get_parameter call')
