# @imports
# Basic imports
import sys
import socket
import threading

from enum import Enum
from time import sleep

# Protobuf imports
import protobuf.stop_pb2 as dti_stop
import protobuf.info_pb2 as dti_info
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
import protobuf.model_info_pb2 as dti_model_info
import protobuf.initialize_pb2 as dti_initialize

from google.protobuf import any_pb2
from google.protobuf.message import Message
from google.protobuf.message import DecodeError

# @classname
FMI2Wrapper

# @constructor
def __init__(self):
    self.state: State = State.UNINITIALIZED
    self.server: socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(target=self.run_server)
    self.model_thread = threading.Thread(target=self.run_model)

# @destructor
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
        return self.return_code(dti_code.INVALID_STATE, f'Cannot initialize in state {self.state.name}')

    ret = # @>callback(initialize)
    if ret.code != dti_code.SUCCESS:
        return ret

    self.state = State.INITIALIZING
    return dti_return.MReturnValue(code=dti_code.SUCCESS)

# @parse(start)
def parse_start(message) -> Message:
    # If the model was not yet initialized, we cannot start
    if self.state == State.UNINITIALIZED:
        return self.return_code(dti_code.INVALID_STATE, f'Cannot start in state {self.state.name}')

    return # @>callback(start)(message)

# @parse(stop)
def parse_stop(message) -> Message:
    ret = # @>callback(stop)(message)
    if ret.code != dti_code.SUCCESS:
        return ret

    self.step = True
    self.state = State.STOPPED
    return dti_return.MReturnValue(code=dti_code.SUCCESS)

# @parse(setinput)
def parse_set_input(message) -> Message:
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

            fval = dti_utils.MF32()
            if value.Unpack(fval):
                return # @>callback(setinput)(identifier, fval.value)
            else:
                return self.return_code(dti_code.INVALID_OPTION, 'Non-float values not yet supported')

            if ret.code != dti_code.SUCCESS:
                return ret

    elif message.identifiers.HasField("ids"):
        n_inputs = len(message.identifiers.ids.ids)
        return # @>callback(setinput)(identifier, fval.value)
        return self.return_code(dti_code.UNKNOWN_OPTION, 'Non-string ids not implemented')
    else:
        return self.return_code(dti_code.INVALID_OPTION, 'No identifiers provided')

    return self.return_code(dti_code.SUCCESS)

# @parse(getoutput)
def parse_get_output(message) -> Message:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dti_code.INVALID_STATE, f'Cannot get output in state {self.state.name}')

    if message.identifiers.HasField("names"):
        n_outputs = len(message.identifiers.names.names)
        values = # @>callback(getoutput)(message.identifiers.names.names)
        if len(values) != n_outputs:
            return self.return_code(dti_code.FAILURE, 'Failed to get all outputs')

        return_value = dti_return.MReturnValue(code=dti_code.SUCCESS)
        for i in range(n_outputs):
            return_value.values.identifiers.names.names.append(message.identifiers.names.names[i])

            # Set the output value
            value = dti_utils.MF32()
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

# @parse(advance)
def parse_advance(message) -> Message:
    if self.state != State.STEPPING:
        return self.return_code(dti_code.INVALID_STATE, f'Cannot advance in state {self.state.name}')

    return # @>callback(advance)(message)

# @parse(initialize)
def parse_initialize(message) -> Message:
    if self.state != State.UNINITIALIZED:
        return self.return_code(dti_code.INVALID_STATE, f'Cannot initialize in state {self.state.name}')

    ret = # @>callback(initialize)(message)
    if ret.code != dti_code.SUCCESS:
        return ret

    self.state = State.INITIALIZING
    return dti_return.MReturnValue(code=dti_code.SUCCESS)

# @parse(modelinfo)
def parse_model_info() -> Message:
    if self.state == State.UNINITIALIZED:
        return self.return_code(dti_code.INVALID_STATE, f'Cannot get model info in state {self.state.name}')

    return # @>callback(modelinfo)()

# @messagehandler
def parse_message(self, data : str) -> Message:
    message = dti_message.MDTMessage()
    try:
        message.ParseFromString(data)
    except DecodeError as e:
        print('Failed to parse incoming message')
        return bytes()

    if message.HasField("stop"):
        return # @>parse(stop)(message.stop)
    elif message.HasField("start"):
        return # @>parse(start)(message.start)
    elif message.HasField("input"):
        return # @>parse(setinput)(message.input.inputs)
    elif message.HasField("output"):
        return # @>parse(getoutput)(message.output.outputs)
    elif message.HasField("advance"):
        return # @>parse(advance)(message.advance)
    elif message.HasField("initialize"):
        return # @>parse(initialize)(message.initialize)
    else:
        return # @>parse(modelinfo)()

    return dti_return.MReturnValue(code=dti_code.UNKNOWN_COMMAND)

# @method
def return_code(self, code: dti_code, message: str = None) -> dti_return:
    if message is None:
        return dti_return.MReturnValue(code=code)

    return dti_return.MReturnValue(code=code, error_message=dti_utils.MString(value=message))

# @method
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

# @method
def parse_and_assign_optional(self, message, name):
    if message.HasField(name):
        return self.parse_number(getattr(message, name))

    return None

# @method
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

# @main
if __name__ == "__main__":
    if len(sys.argv) > 0:
        PORT = int(sys.argv[1])

    print(f'Running with port: {PORT}')

    wrapper = # @>classname()
    wrapper.run()

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
