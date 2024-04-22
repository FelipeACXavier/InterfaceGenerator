<DTIG_IMPORTS>
# Basic imports
import sys
import socket
import threading

from enum import Enum
from time import sleep

# Protobuf imports
import dtig.info_pb2 as dtig_info
import dtig.utils_pb2 as dtig_utils
import dtig.state_pb2 as dtig_state
import dtig.status_pb2 as dtig_status
import dtig.values_pb2 as dtig_values
import dtig.return_code_pb2 as dtig_code
import dtig.run_mode_pb2 as dtig_run_mode
import dtig.dt_message_pb2 as dtig_message
import dtig.return_value_pb2 as dtig_return

from google.protobuf import any_pb2
from google.protobuf.message import Message
from google.protobuf.message import DecodeError

<DTIG_CLASSNAME>
PythonWrapper

<DTIG_CONSTRUCTOR(PUBLIC)>
def __init__(self):
    self.mode = dtig_run_mode.UNKNOWN
    self.state = dtig_state.UNINITIALIZED
    self.server: socket.socket = None

    self.lock = threading.Lock()
    self.condition = threading.Condition(lock=self.lock)

    self.server_thread = threading.Thread(
        target=DTIG>CALLBACK(RUNSERVER)
    )
    self.model_thread = threading.Thread(
        target=DTIG>CALLBACK(RUNMODEL)
    )

<DTIG_DESTRUCTOR(PUBLIC)>
def __del__(self):
    if self.server is not None:
        self.server.close()

<DTIG_RUN>
def run(self) -> None:
    if not self.create_connection():
        return

    self.server_thread.start()
    self.model_thread.start()

    self.server_thread.join()
    self.model_thread.join()

<DTIG_PARSE(INITIALIZE)>
def parse_initialize(message) -> Message:
    if self.state != dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot initialize in state {dtig_state.EState.Name(self.state)}')

    ret = DTIG>CALLBACK(INITIALIZE)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.state = dtig_state.INITIALIZED
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_PARSE(START)>
def parse_start(message) -> Message:
    # If the model was not yet initialized, we cannot start
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot start in state {dtig_state.EState.Name(self.state)}')

    return DTIG>CALLBACK(START)(message)

<DTIG_PARSE(STOP)>
def parse_stop(message) -> Message:
    ret = DTIG>CALLBACK(STOP)(message)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.step = True
    self.state = dtig_state.STOPPED
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_PARSE(SET_INPUT)>
def parse_set_input(message) -> Message:
    # If the model was not yet initialized, we cannot set inputs
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot set input in state {dtig_state.EState.Name(self.state)}')

    ids_length = len(message.inputs.identifiers)
    for i in range(ids_length):
        identifier : str = message.inputs.identifiers[i]
        any_value : any_pb2.Any = message.inputs.values[i]

        # Only the model knows the type, unpacking must be a responsibility of the callback function
        ret = DTIG>CALLBACK(SET_INPUT)(identifier, any_value)
        if ret.code != dtig_code.SUCCESS:
            return ret

    return self.return_code(dtig_code.SUCCESS)

<DTIG_PARSE(GET_OUTPUT)>
def parse_get_output(message) -> dtig_return.MReturnValue:
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get output in state {dtig_state.EState.Name(self.state)}')

    ids_length = len(message.outputs.identifiers)
    return_message = DTIG>CALLBACK(GET_OUTPUT)(message.outputs.identifiers)
    if len(return_message.values.identifiers) != ids_length and return_message.code == dtig_code.SUCCESS:
        return_message.code = dtig_code.FAILURE
        return_message.error_message.value = 'Failed to get all outputs'

    return return_message

<DTIG_PARSE(SET_PARAMETER)>
def parse_set_parameter(message) -> dtig_return.MReturnValue:
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot set parameter in state {dtig_state.EState.Name(self.state)}')

    ids_length = len(message.parameters.identifiers)
    for i in range(ids_length):
        identifier : str = message.parameters.identifiers[i]
        any_value : any_pb2.Any = message.parameters.values[i]

        # Only the model knows the type, unpacking must be a responsibility of the callback function
        ret = DTIG>CALLBACK(SET_PARAMETER)(identifier, any_value)
        if ret.code != dtig_code.SUCCESS:
            return ret

    return self.return_code(dtig_code.SUCCESS)

<DTIG_PARSE(GET_PARAMETER)>
def parse_get_parameter(message) -> dtig_return.MReturnValue:
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get parameter in state {dtig_state.EState.Name(self.state)}')

    ids_length = len(message.parameters.identifiers)
    return_message = DTIG>CALLBACK(GET_PARAMETER)(message.parameters.identifiers)
    if len(return_message.values.identifiers) != ids_length and return_message.code == dtig_code.SUCCESS:
        return_message.code = dtig_code.FAILURE
        return_message.error_message.value = 'Failed to get all parameters'

    return return_message

<DTIG_PARSE(ADVANCE)>
def parse_advance(message) -> Message:
    if self.state != dtig_state.WAITING:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot advance in state {dtig_state.EState.Name(self.state)}')

    return DTIG>CALLBACK(ADVANCE)(message)

<DTIG_PARSE(INITIALIZE)>
def parse_initialize(message) -> Message:
    if self.state != dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot initialize in state {dtig_state.EState.Name(self.state)}')

    ret = DTIG>CALLBACK(INITIALIZE)(message)
    if ret.code != dtig_code.SUCCESS:
        return ret

    self.state = dtig_state.INITIALIZED
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_PARSE(MODEL_INFO)>
def parse_model_info() -> Message:
    if self.state == dtig_state.UNINITIALIZED:
        return self.return_code(dtig_code.INVALID_STATE, f'Cannot get model info in state {dtig_state.EState.Name(self.state)}')

    return DTIG>CALLBACK(MODEL_INFO)()

<DTIG_PARSE(GET_STATUS)>
def parse_get_status() -> Message:
    return DTIG>CALLBACK(GET_STATUS)()

<DTIG_MESSAGEHANDLER>
def parse_message(self, data : str) -> Message:
    message = dtig_message.MDTMessage()
    try:
        message.ParseFromString(data)
    except DecodeError as e:
        print('Failed to parse incoming message')
        return bytes()

    if message.HasField("advance"):
        return DTIG>PARSE(ADVANCE)(message.advance)
    elif message.HasField("set_input"):
        return DTIG>PARSE(SET_INPUT)(message.set_input)
    elif message.HasField("get_output"):
        return DTIG>PARSE(GET_OUTPUT)(message.get_output)
    elif message.HasField("initialize"):
        return DTIG>PARSE(INITIALIZE)(message.initialize)
    elif message.HasField("start"):
        return DTIG>PARSE(START)(message.start)
    elif message.HasField("stop"):
        return DTIG>PARSE(STOP)(message.stop)
    elif message.HasField("set_parameter"):
        return DTIG>PARSE(SET_PARAMETER)(message.set_parameter)
    elif message.HasField("get_parameter"):
        return DTIG>PARSE(GET_PARAMETER)(message.get_parameter)
    elif message.HasField("get_status"):
        return DTIG>PARSE(GET_STATUS)()
    else:
        return DTIG>PARSE(MODEL_INFO)()

    return dtig_return.MReturnValue(code=dtig_code.UNKNOWN_COMMAND)

<DTIG_METHOD(PUBLIC)>
def return_code(self, code: dtig_code, message: str = None) -> dtig_return:
    if message is None:
        return dtig_return.MReturnValue(code=code)

    return dtig_return.MReturnValue(code=code, error_message=dtig_utils.MString(value=message))

<DTIG_METHOD(PUBLIC)>
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

<DTIG_RUNSERVER>
def run_server(self) -> None:
    sock, addr = self.server.accept()
    with sock:
        print(f"{addr} connected in state {dtig_state.EState.Name(self.state)}")
        try:
            while True:
                # Wait for client command
                data: str = sock.recv(1024)
                if not data:
                    print("Client disconnected")
                    break

                # Parse client command
                with self.condition:
                    reply: bytes = DTIG>MESSAGEHANDLER(data).SerializeToString()
                    sock.sendall(reply)
                    self.condition.notify_all()

                    if self.state == dtig_state.STOPPED:
                        break

        except Exception as e:
            print(f'Failed: {e}')
            sock.sendall(''.encode())
            sleep(1)

        with self.condition:
            self.step = True
            self.state = dtig_state.STOPPED
            self.condition.notify_all()

<DTIG_MAIN>
if __name__ == "__main__":
    print(sys.argv)
    for i, arg in enumerate(sys.argv):
        if arg == "--host":
            HOST = sys.argv[i + 1]
        elif arg == "--port":
            PORT = int(sys.argv[i + 1])

    wrapper = DTIG>CLASSNAME()
    wrapper.DTIG>RUN()

<DTIG_STATES>
HOST = "127.0.0.1"
PORT = 8080

<DTIG_CALLBACK(INITIALIZE)>
def initialize_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support initialize call')

<DTIG_CALLBACK(ADVANCE)>
def advance_callback(self, message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support advance call')

<DTIG_CALLBACK(STOP)>
def stop_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support stop call')

<DTIG_CALLBACK(START)>
def start_callback(message) -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support start call')

<DTIG_CALLBACK(MODEL_INFO)>
def get_model_info():
    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)

    # Inputs
    DTIG_FOR(DTIG_INPUTS)
    info_DTIG_ITEM_NAME = dtig_info.MInfo()

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME.id.value = DTIG_ITEM_ID
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME.name.value = DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME.description.value = DTIG_STR(DTIG_ITEM_DESCRIPTION)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME.type.value = DTIG_STR(DTIG_ITEM_TYPE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME.unit.value = DTIG_STR(DTIG_ITEM_UNIT)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME.namespace.value = DTIG_STR(DTIG_ITEM_NAMESPACE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME.default.value = DTIG_STR(DTIG_ITEM_DEFAULT)
    DTIG_END_IF

    return_value.model_info.inputs.append(info_DTIG_ITEM_NAME)
    DTIG_END_FOR

    # Outputs
    DTIG_FOR(DTIG_OUTPUTS)
    info_DTIG_ITEM_NAME = dtig_info.MInfo()

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME.id.value = DTIG_ITEM_ID
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME.name.value = DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME.description.value = DTIG_STR(DTIG_ITEM_DESCRIPTION)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME.type.value = DTIG_STR(DTIG_ITEM_TYPE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME.unit.value = DTIG_STR(DTIG_ITEM_UNIT)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME.namespace.value = DTIG_STR(DTIG_ITEM_NAMESPACE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME.default.value = DTIG_STR(DTIG_ITEM_DEFAULT)
    DTIG_END_IF

    return_value.model_info.outputs.append(info_DTIG_ITEM_NAME)
    DTIG_END_FOR

    # Parameters
    DTIG_FOR(DTIG_PARAMETERS)
    info_DTIG_ITEM_NAME = dtig_info.MInfo()

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME.id.value = DTIG_ITEM_ID
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME.name.value = DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME.description.value = DTIG_STR(DTIG_ITEM_DESCRIPTION)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME.type.value = DTIG_STR(DTIG_ITEM_TYPE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME.unit.value = DTIG_STR(DTIG_ITEM_UNIT)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME.namespace.value = DTIG_STR(DTIG_ITEM_NAMESPACE)
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME.default.value = DTIG_STR(DTIG_ITEM_DEFAULT)
    DTIG_END_IF

    return_value.model_info.parameters.append(info_DTIG_ITEM_NAME)
    DTIG_END_FOR

    return return_value

<DTIG_CALLBACK(SET_INPUT)>
def set_input_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support set_input call')

<DTIG_CALLBACK(GET_OUTPUT)>
def get_output_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support get_output call')

<DTIG_CALLBACK(SET_PARAMETER)>
def set_parameter_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support set_parameter call')

<DTIG_CALLBACK(GET_PARAMETER)>
def get_parameter_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support get_parameter call')

<DTIG_CALLBACK(GET_STATUS)>
def get_status_callback() -> Message:
    return self.return_code(dtig_code.UNKNOWN_OPTION, f'Engine does not support get_status call')
