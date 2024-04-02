import os
import subprocess

from dtig.common.result import VoidResult

DEFAULT_INDENTATION = "  "

def set_indentation(data : str, level : int = 1) -> str:
  indentation = str()
  for i in range(level):
    indentation += DEFAULT_INDENTATION

  new_data = str()
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
            first_character = len(line) - l_line

            # Use spaces instead of tabs
            data += line.replace("\t", DEFAULT_INDENTATION)
    return data