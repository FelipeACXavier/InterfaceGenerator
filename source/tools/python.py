import os
import subprocess

from common.keys import *
from common.result import VoidResult
from common.default_structure import create_default_structure

DEFAULT_INDENTATION = "    "

def format(filename : str) -> VoidResult:
    bin_dir = os.environ['VIRTUAL_ENV'] + "/bin/"
    command = f"{bin_dir}autopep8 {filename} --aggressive --select=E1,W1 -i"

    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
      return VoidResult.failed(f'Failed to format generated file: {result.stderr}')

    return VoidResult()

def set_indentation(data : str, level : int = 1) -> str:
  indentation = ""
  for i in range(level):
    indentation += DEFAULT_INDENTATION

  new_data = ""
  data_with_breaks = data.splitlines(keepends=True)
  for line in data_with_breaks:
    new_data += indentation + line

  return new_data

# TODO: This is not robust at all :p
def read_file(file : str) -> str:
    data = ""
    with open(file, "r") as file:
        for line in file.readlines():
            # Ignore comments
            l_line = len(line.lstrip())

            # Use spaces instead of tabs
            data += line.replace("\t", DEFAULT_INDENTATION)
    return data

def to_type(variable_type):
    if variable_type == TYPE_FLOAT_32:
        return f'float'
    elif variable_type == TYPE_FLOAT_64:
        return f'float'
    elif variable_type == TYPE_INT_8:
        return f'int'
    elif variable_type == TYPE_INT_16:
        return f'int'
    elif variable_type == TYPE_INT_32:
        return f'int'
    elif variable_type == TYPE_INT_64:
        return f'int'
    elif variable_type == TYPE_UINT_8:
        return f'int'
    elif variable_type == TYPE_UINT_16:
        return f'int'
    elif variable_type == TYPE_UINT_32:
        return f'int'
    elif variable_type == TYPE_UINT_64:
        return f'int'
    elif variable_type == TYPE_STRING:
        return f'str'
    elif variable_type == TYPE_BOOL:
        return f'bool'
    elif variable_type == TYPE_BYTES:
        return f'bytes'

def to_proto_message(variable_type):
    if variable_type == TYPE_FLOAT_32:
        return f'dtig_utils.MF32()'
    elif variable_type == TYPE_FLOAT_64:
        return f'dtig_utils.MF64()'
    elif variable_type == TYPE_INT_8:
        return f'dtig_utils.MI8()'
    elif variable_type == TYPE_INT_16:
        return f'dtig_utils.MI16()'
    elif variable_type == TYPE_INT_32:
        return f'dtig_utils.MI32()'
    elif variable_type == TYPE_INT_64:
        return f'dtig_utils.MI64()'
    elif variable_type == TYPE_UINT_8:
        return f'dtig_utils.MU8()'
    elif variable_type == TYPE_UINT_16:
        return f'dtig_utils.MU16()'
    elif variable_type == TYPE_UINT_32:
        return f'dtig_utils.MU32()'
    elif variable_type == TYPE_UINT_64:
        return f'dtig_utils.MU64()'
    elif variable_type == TYPE_STRING:
        return f'dtig_utils.MString()'
    elif variable_type == TYPE_BOOL:
        return f'dtig_utils.MBool()'
    elif variable_type == TYPE_BYTES:
        return f'dtig_utils.MBytes()'
    elif variable_type == TYPE_FIXTURE:
        return f'dtig_utils.MConstraint()'
    elif variable_type == TYPE_FORCE:
        return f'dtig_utils.MConstraint()'
    elif variable_type == TYPE_MATERIAL:
        return f'dtig_utils.MMaterial()'
    elif variable_type == TYPE_MESH:
        return f'dtig_utils.MString()'

def create_structure():
    structure = create_default_structure()
    structure[KEY_RUN][KEY_NAME]                            = "dtig_run"
    structure[KEY_RUN_MODEL][KEY_NAME]                      = "dtig_run_model"
    structure[KEY_RUN_SERVER][KEY_NAME]                     = "dtig_run_server"
    structure[KEY_RUN_CLIENT][KEY_NAME]                     = "dtig_run_client"
    structure[KEY_MESSAGE_HANDLER][KEY_NAME]                = "dtig_handle_message"

    structure[KEY_PARSE][KEY_STOP][KEY_NAME]                = "dtig_stop"
    structure[KEY_PARSE][KEY_START][KEY_NAME]               = "dtig_start"
    structure[KEY_PARSE][KEY_ADVANCE][KEY_NAME]             = "dtig_advance"
    structure[KEY_PARSE][KEY_PUBLISH][KEY_NAME]             = "dtig_publishers"
    structure[KEY_PARSE][KEY_SUBSCRIBE][KEY_NAME]           = "dtig_subscribers"
    structure[KEY_PARSE][KEY_SET_INPUT][KEY_NAME]           = "dtig_set_input"
    structure[KEY_PARSE][KEY_GET_OUTPUT][KEY_NAME]          = "dtig_get_output"
    structure[KEY_PARSE][KEY_INITIALIZE][KEY_NAME]          = "dtig_initialize"
    structure[KEY_PARSE][KEY_MODEL_INFO][KEY_NAME]          = "dtig_model_info"
    structure[KEY_PARSE][KEY_GET_STATUS][KEY_NAME]          = "dtig_get_status"
    structure[KEY_PARSE][KEY_SET_PARAMETER][KEY_NAME]       = "dtig_set_parameter"
    structure[KEY_PARSE][KEY_GET_PARAMETER][KEY_NAME]       = "dtig_get_parameter"

    structure[KEY_CALLBACK][KEY_RUN][KEY_NAME]              = structure[KEY_RUN][KEY_NAME]
    structure[KEY_CALLBACK][KEY_RUN_MODEL][KEY_NAME]        = structure[KEY_RUN_MODEL][KEY_NAME]
    structure[KEY_CALLBACK][KEY_RUN_SERVER][KEY_NAME]       = structure[KEY_RUN_SERVER][KEY_NAME]
    structure[KEY_CALLBACK][KEY_RUN_CLIENT][KEY_NAME]       = structure[KEY_RUN_CLIENT][KEY_NAME]

    structure[KEY_CALLBACK][KEY_STOP][KEY_NAME]             = "dtig_engine_stop"
    structure[KEY_CALLBACK][KEY_START][KEY_NAME]            = "dtig_engine_start"
    structure[KEY_CALLBACK][KEY_ADVANCE][KEY_NAME]          = "dtig_engine_advance"
    structure[KEY_CALLBACK][KEY_PUBLISH][KEY_NAME]          = "dtig_engine_publish"
    structure[KEY_CALLBACK][KEY_SUBSCRIBE][KEY_NAME]        = "dtig_engine_subscribe"
    structure[KEY_CALLBACK][KEY_SET_INPUT][KEY_NAME]        = "dtig_engine_set_input"
    structure[KEY_CALLBACK][KEY_GET_OUTPUT][KEY_NAME]       = "dtig_engine_get_output"
    structure[KEY_CALLBACK][KEY_INITIALIZE][KEY_NAME]       = "dtig_engine_initialize"
    structure[KEY_CALLBACK][KEY_MODEL_INFO][KEY_NAME]       = "dtig_engine_model_info"
    structure[KEY_CALLBACK][KEY_GET_STATUS][KEY_NAME]       = "dtig_engine_get_status"
    structure[KEY_CALLBACK][KEY_SET_PARAMETER][KEY_NAME]    = "dtig_engine_set_parameter"
    structure[KEY_CALLBACK][KEY_GET_PARAMETER][KEY_NAME]    = "dtig_engine_get_parameter"

    return structure