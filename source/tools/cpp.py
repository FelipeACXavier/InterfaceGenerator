import os

from common.result import VoidResult

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