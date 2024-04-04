import os
import subprocess

from common.keys import *
from common.result import VoidResult

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