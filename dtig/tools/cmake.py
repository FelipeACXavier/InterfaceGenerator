import os

from dtig.common.logging import LOG_DEBUG
from dtig.common.result import VoidResult
from dtig.base.compiler_base import CompilerBase

class CMakeCompiler(CompilerBase):
    def __init__(self, output_file):
        super().__init__(os.path.dirname(output_file) + "/CMakeLists.txt")

    def compile(self) -> VoidResult:
        if not self.version:
            return VoidResult.failed("No tool version defined")

        body = f'cmake_minimum_required(VERSION {self.version})\n\n'

        body += 'include(GNUInstallDirs)\n'
        body += 'include(CMakePrintHelpers)\n\n'

        body += "file(GLOB SOURCES\n"
        for source in self.sources:
            body += f'  {source["path"]}\n'
        body += ")\n\n"

        for include in self.include_dirs:
            path = f'${{PROJECT_SOURCE_DIR}}{include["path"]}' if include["relative"] else include["path"]
            body += f'include_directories({path})\n'
        body += "\n"

        for library in self.library_dirs:
            path = f'${{PROJECT_SOURCE_DIR}}{library["path"]}' if library["relative"] else library["path"]
            body += f'link_directories({path})\n'
        body += "\n"

        body += f'add_executable(${{PROJECT_NAME}} {self.sources[0]["path"]} ${{SOURCES}})\n'
        body += f'set_target_properties(${{PROJECT_NAME}} PROPERTIES VERSION {self.version})\n\n'

        for library in self.libraries:
            body += f'target_link_libraries(${{PROJECT_NAME}} {library})\n'

        LOG_DEBUG(f'Writing cmake file to {self.output_file}')
        with open(self.output_file, "w") as file:
            file.write(body)

        return VoidResult()

