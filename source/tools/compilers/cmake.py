import os

from tools.file_system import *
from common.result import VoidResult
from common.logging import LOG_DEBUG
from base.compiler_base import CompilerBase

class CMakeCompiler(CompilerBase):
    def __init__(self, output_file):
        super().__init__(os.path.dirname(output_file) + "/CMakeLists.txt")
        self.set_compiler("cmake")

    def compile(self, options = []) -> VoidResult:
        base_dir = os.path.dirname(self.output_file)
        build_dir = base_dir + "/build"
        install_dir = base_dir + "/install"

        LOG_DEBUG(f'Compiling to folder: {build_dir}')

        cmake_cmd = f'{self.compiler} -DCMAKE_INSTALL_PREFIX={install_dir} .. && make -j4'
        for opt in options:
            if "install" in opt:
                if not is_directory_empty(install_dir):
                    LOG_INFO("Already installed")
                    return VoidResult()

                LOG_DEBUG(f'Installing to folder: {install_dir}')
                cmake_cmd += "&& make install"

        create_dir(build_dir)
        create_dir(install_dir)

        cd_cmd = f'cd {build_dir}'
        built = run_command(f'{cd_cmd} && {cmake_cmd}')
        if not built:
            return built

        return VoidResult()

    def generate(self) -> VoidResult:
        if not self.version:
            return VoidResult.failed("No tool version defined")

        body = f'cmake_minimum_required(VERSION {self.version})\n\n'

        body += 'include(GNUInstallDirs)\n'
        body += 'include(CMakePrintHelpers)\n\n'

        if self.project:
            body += f'project({self.project} VERSION 1.0)\n'

        if len(self.compiler_opts) > 0:
            for opt in self.compiler_opts:
                body += f'add_compile_options({opt})\n'

        if len(self.sources) > 0:
            body += "file(GLOB SOURCES\n"
            for source in self.sources:
                body += f'  {source["path"]}\n'
            body += ")\n\n"

        if len(self.include_dirs) > 0:
            for include in self.include_dirs:
                path = f'${{PROJECT_SOURCE_DIR}}{include["path"]}' if include["relative"] else include["path"]
                body += f'include_directories({path})\n'
            body += "\n"

        if len(self.library_dirs) > 0:
            for library in self.library_dirs:
                path = f'${{PROJECT_SOURCE_DIR}}{library["path"]}' if library["relative"] else library["path"]
                body += f'link_directories({path})\n'
            body += "\n"

        if len(self.sources) > 0:
            body += f'add_executable(${{PROJECT_NAME}} {self.sources[0]["path"]} ${{SOURCES}})\n'
            body += f'set_target_properties(${{PROJECT_NAME}} PROPERTIES VERSION {self.version})\n\n'

        if len(self.libraries) > 0:
            for library in self.libraries:
                body += f'target_link_libraries(${{PROJECT_NAME}} {library})\n'

        if len(self.subfolders) > 0:
            for folder in self.subfolders:
                body += f'add_subdirectory({folder})\n'

        LOG_DEBUG(f'Writing cmake file to {self.output_file}')
        with open(self.output_file, "w") as file:
            file.write(body)

        return VoidResult()

    def install(self, version, installation_dir=None) -> VoidResult:
        return VoidResult()