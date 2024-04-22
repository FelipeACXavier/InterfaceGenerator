<DTIG_IMPORTS>
import sys
import socket
import argparse

from common.logging import *

# Import protobuf files once they were created
from google.protobuf import message
from google.protobuf import any_pb2
from google.protobuf import wrappers_pb2

import dtig.state_pb2 as dtig_state
import dtig.utils_pb2 as dtig_utils
import dtig.values_pb2 as dtig_values
import dtig.return_code_pb2 as dtig_code
import dtig.run_mode_pb2 as dtig_run_mode
import dtig.dt_message_pb2 as dtig_message
import dtig.stop_mode_pb2 as dtig_stop_mode
import dtig.return_value_pb2 as dtig_return

argument_parser = argparse.ArgumentParser(description='Python DTIG client')
argument_parser.add_argument('-i', action="store", dest="hostname", help='Hostname of the server', default="127.0.0.1")
argument_parser.add_argument('-p', action="store", dest="port", help='Port of the server', default=8080)
argument_parser.add_argument('-m', action="store", dest="model_name", help='Model name', default=None)
cmd_args = argument_parser.parse_args()

<DTIG_CLASSNAME>
Client

<DTIG_CONSTRUCTOR(PUBLIC)>
def __init__(self, cmd_args):
    self.running = True
    self.model_name = cmd_args.model_name
    self.hostname = cmd_args.hostname
    self.port = cmd_args.port

<DTIG_RUN>
def run(self):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((self.hostname, self.port))
        DTIG>CALLBACK(RUNCLIENT)(s)

<DTIG_PARSE(STOP)>
def stop(self, sock):
    DTIG>CALLBACK(STOP)(sock)
    LOG_WARNING("Stopping client")
    self.running = False

<DTIG_PARSE(INITIALIZE)>
def initialize(self, sock):
    DTIG>CALLBACK(INITIALIZE)(sock)

<DTIG_PARSE(START)>
def run_stepped(self, sock):
    DTIG>CALLBACK(START)(sock)

<DTIG_PARSE(ADVANCE)>
def advance(self, sock):
    DTIG>CALLBACK(ADVANCE)(sock)

<DTIG_PARSE(SET_INPUT)>
def set_input(self, sock):
    DTIG>CALLBACK(SET_INPUT)(sock)

<DTIG_PARSE(GET_OUTPUT)>
def get_output(self, sock):
    DTIG>CALLBACK(GET_OUTPUT)(sock)

<DTIG_PARSE(SET_PARAMETER)>
def set_parameter(self, sock):
    DTIG>CALLBACK(SET_PARAMETER)(sock)

<DTIG_PARSE(GET_PARAMETER)>
def get_parameter(self, sock):
    DTIG>CALLBACK(GET_PARAMETER)(sock)

<DTIG_PARSE(MODEL_INFO)>
def model_info(self, sock):
    DTIG>CALLBACK(MODEL_INFO)(sock)

<DTIG_PARSE(GET_STATUS)>
def status(self, sock):
    DTIG>CALLBACK(GET_STATUS)(sock)

<DTIG_MAIN>
if __name__ == "__main__":
    start_logger(LogLevel.DEBUG)
    cmd_args = argument_parser.parse_args()

    wrapper = DTIG>CLASSNAME(cmd_args)
    wrapper.DTIG>RUN()