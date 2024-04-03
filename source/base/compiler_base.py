import os
from abc import abstractmethod

from common.result import VoidResult

ENV_DIR = os.environ['VIRTUAL_ENV'] + "/"
INCLUDE_DIR = ENV_DIR + "include"
LIB_DIR = ENV_DIR + "lib"

class CompilerBase():
    def __init__(self, output_file):
        self.output_file = output_file
        self.project = None
        self.version = None

        self.sources = []
        self.libraries = []
        self.include_dirs = [{"path": INCLUDE_DIR, "relative": False}]
        self.library_dirs = [{"path": LIB_DIR,     "relative": False}]

        self.compiler_opts = []
        self.subfolders = []

    @abstractmethod
    def compile(self, options = []) -> VoidResult:
        raise Exception("compile must be implemented")

    @abstractmethod
    def generate(self) -> VoidResult:
        raise Exception("generate must be implemented")

    def set_project(self, project : str):
        self.project = project

    def add_option(self, opt : str):
        self.compiler_opts.append(opt)

    def add_subfolder(self, folder : str):
        self.subfolders.append(folder)

    def add_source(self, opt : str, relative = True):
        self.sources.append({"path": opt, "relative" : relative})

    def add_include_dir(self, opt : str, relative = True):
        self.include_dirs.append({"path": opt, "relative" : relative})

    def add_library(self, opt : str):
        self.libraries.append(opt)

    def add_library_dir(self, opt : str, relative = True):
        self.library_dirs.append({"path": opt, "relative" : relative})

    def add_version(self, version):
        self.version = version