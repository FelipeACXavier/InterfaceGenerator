import os
import subprocess

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