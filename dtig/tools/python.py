import os
import subprocess

from dtig.common.result import VoidResult

DEFAULT_INDENTATION = "    "

def format(file) -> VoidResult:
    bin_dir = os.environ['VIRTUAL_ENV'] + "/bin/"
    command = f"{bin_dir}autopep8 {file} --aggressive --select=E1,W1 -i"

    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
      return VoidResult.failed(f'Failed to format generated file: {result.stderr}')

    return VoidResult()

def set_indentation(data, level : int = 1):
  indentation = str()
  for i in range(level):
    indentation += DEFAULT_INDENTATION

  new_data = str()
  data_with_breaks = data.splitlines(keepends=True)
  for line in data_with_breaks:
    new_data += indentation + line

  return new_data

# TODO: This is not robust at all :p
def read_file(file):
    data = ""
    with open(file, "r") as file:
        for line in file.readlines():
            # Ignore comments
            l_line = len(line.lstrip())
            first_character = len(line) - l_line
            if l_line > 0 and line[first_character] == "#":
                continue

            # Use spaces instead of tabs
            data += line.replace("\t", DEFAULT_INDENTATION)
    return data