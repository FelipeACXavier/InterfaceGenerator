import os

from common.keys import *
from common.result import VoidResult
from common.default_structure import create_default_structure

DEFAULT_INDENTATION = "  "

def read_file(file : str) -> str:
    data = ""
    with open(file, "r") as file:
        for line in file.readlines():
            # Ignore comments
            l_line = len(line.lstrip())
            first_character = len(line) - l_line

            # Use spaces instead of tabs
            data += line.replace("\t", DEFAULT_INDENTATION)
    return data

def set_indentation(data : str) -> str:
  new_data = ""
  indentation = ""

  data_with_breaks = data.splitlines(keepends=True)
  for line in data_with_breaks:
    if "}" in line and not "{" in line:
        indentation = indentation[:-2]

    if "public:" in line or "private:" in line:
        new_data += line
    else:
        new_data += indentation + line

    if "{" in line and not "}" in line:
        indentation += DEFAULT_INDENTATION

  return new_data

def to_type(variable_type):
    if variable_type == TYPE_FLOAT_32:
        return f'float'
    elif variable_type == TYPE_FLOAT_64:
        return f'double'
    elif variable_type == TYPE_INT_8:
        return f'int8_t'
    elif variable_type == TYPE_INT_16:
        return f'int16_t'
    elif variable_type == TYPE_INT_32:
        return f'int32_t'
    elif variable_type == TYPE_INT_64:
        return f'int64_t'
    elif variable_type == TYPE_UINT_8:
        return f'uint8_t'
    elif variable_type == TYPE_UINT_16:
        return f'uint16_t'
    elif variable_type == TYPE_UINT_32:
        return f'uint32_t'
    elif variable_type == TYPE_UINT_64:
        return f'uint64_t'
    elif variable_type == TYPE_STRING:
        return f'std::string'
    elif variable_type == TYPE_BOOL:
        return f'bool'
    elif variable_type == TYPE_BYTES:
        return f'std::string'

def to_proto_message(variable_type):
    if variable_type == TYPE_FLOAT_32:
        return f'dtig::MF32'
    elif variable_type == TYPE_FLOAT_64:
        return f'dtig::MF64'
    elif variable_type == TYPE_INT_8:
        return f'dtig::MI8'
    elif variable_type == TYPE_INT_16:
        return f'dtig::MI16'
    elif variable_type == TYPE_INT_32:
        return f'dtig::MI32'
    elif variable_type == TYPE_INT_64:
        return f'dtig::MI64'
    elif variable_type == TYPE_UINT_8:
        return f'dtig::MU8'
    elif variable_type == TYPE_UINT_16:
        return f'dtig::MU16'
    elif variable_type == TYPE_UINT_32:
        return f'dtig::MU32'
    elif variable_type == TYPE_UINT_64:
        return f'dtig::MU64'
    elif variable_type == TYPE_STRING:
        return f'dtig::MString'
    elif variable_type == TYPE_BOOL:
        return f'dtig::MBool'
    elif variable_type == TYPE_BYTES:
        return f'dtig::MBytes'

def create_structure():
    structure = create_default_structure()
    structure[KEY_RUN][KEY_NAME]                            = "dtigRun"
    structure[KEY_RUN_MODEL][KEY_NAME]                      = "dtigRunModel"
    structure[KEY_RUN_SERVER][KEY_NAME]                     = "dtigRunServer"
    structure[KEY_RUN_CLIENT][KEY_NAME]                     = "dtigRunClient"
    structure[KEY_MESSAGE_HANDLER][KEY_NAME]                = "dtigHandleMessage"

    structure[KEY_PARSE][KEY_STOP][KEY_NAME]                = "dtigStop"
    structure[KEY_PARSE][KEY_START][KEY_NAME]               = "dtigStart"
    structure[KEY_PARSE][KEY_ADVANCE][KEY_NAME]             = "dtigAdvance"
    structure[KEY_PARSE][KEY_PUBLISH][KEY_NAME]             = "dtigPublishers"
    structure[KEY_PARSE][KEY_SUBSCRIBE][KEY_NAME]           = "dtigSubscribers"
    structure[KEY_PARSE][KEY_SET_INPUT][KEY_NAME]           = "dtigSetInput"
    structure[KEY_PARSE][KEY_GET_OUTPUT][KEY_NAME]          = "dtigGetOutput"
    structure[KEY_PARSE][KEY_INITIALIZE][KEY_NAME]          = "dtigInitialize"
    structure[KEY_PARSE][KEY_MODEL_INFO][KEY_NAME]          = "dtigModelInfo"
    structure[KEY_PARSE][KEY_SET_PARAMETER][KEY_NAME]       = "dtigSetParameter"
    structure[KEY_PARSE][KEY_GET_PARAMETER][KEY_NAME]       = "dtigGetParameter"

    structure[KEY_CALLBACK][KEY_RUN][KEY_NAME]              = structure[KEY_RUN][KEY_NAME]
    structure[KEY_CALLBACK][KEY_RUN_MODEL][KEY_NAME]        = structure[KEY_RUN_MODEL][KEY_NAME]

    structure[KEY_CALLBACK][KEY_STOP][KEY_NAME]             = "dtigEngineStop"
    structure[KEY_CALLBACK][KEY_START][KEY_NAME]            = "dtigEngineStart"
    structure[KEY_CALLBACK][KEY_ADVANCE][KEY_NAME]          = "dtigEngineAdvance"
    structure[KEY_CALLBACK][KEY_PUBLISH][KEY_NAME]          = "dtigEnginePublish"
    structure[KEY_CALLBACK][KEY_SUBSCRIBE][KEY_NAME]        = "dtigEngineSubscribe"
    structure[KEY_CALLBACK][KEY_SET_INPUT][KEY_NAME]        = "dtigEngineSetInput"
    structure[KEY_CALLBACK][KEY_GET_OUTPUT][KEY_NAME]       = "dtigEngineGetOutput"
    structure[KEY_CALLBACK][KEY_INITIALIZE][KEY_NAME]       = "dtigEngineInitialize"
    structure[KEY_CALLBACK][KEY_MODEL_INFO][KEY_NAME]       = "dtigEngineModelInfo"
    structure[KEY_CALLBACK][KEY_SET_PARAMETER][KEY_NAME]    = "dtigEngineSetParameter"
    structure[KEY_CALLBACK][KEY_GET_PARAMETER][KEY_NAME]    = "dtigEngineGetParameter"

    return structure


