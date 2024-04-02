import os

from dtig.common.result import VoidResult

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

def set_indentation(data : str, level : int = 1) -> str:
  indentation = str()
  for i in range(level):
    indentation += DEFAULT_INDENTATION

  new_data = str()
  data_with_breaks = data.splitlines(keepends=True)
  for line in data_with_breaks:
    if "public:" in line or "private:" in line:
        new_data += line
    else:
        new_data += indentation + line


  return new_data