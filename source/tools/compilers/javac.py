import re
import sys

from tools.file_system import *
from common.result import VoidResult
from common.logging import LOG_DEBUG
from base.compiler_base import CompilerBase

class JavaCompiler(CompilerBase):
    def __init__(self, output_file):
        super().__init__(output_file)
        self.set_compiler("javac")

    def compile(self, options = []) -> VoidResult:
        if not len(self.sources):
            return VoidResult.failed("No sources provided")

        if not exists(self.compiler):
            return VoidResult.failed(f'Compiler: {self.compiler} is not installed')

        base_dir = os.path.dirname(self.output_file)
        build_dir = base_dir + "/build"

        LOG_DEBUG(f'Compiling to folder: {build_dir}')

        build_cmd = f'{self.compiler} -d {build_dir} '
        lib_divider = ";" if sys.platform == "win32" else ":"
        if len(self.library_dirs) > 0:
            build_cmd += "-cp "
            for library in self.library_dirs:
                build_cmd += f'{library["path"]}{lib_divider}'

        # Remove trailing separator
        build_cmd = build_cmd.strip(lib_divider) + " "

        for source in self.sources:
            build_cmd += f'{source["path"]}'

        create_dir(build_dir)

        LOG_DEBUG(f'Running: {build_cmd}')
        cd_cmd = f'cd {base_dir}'
        built = run_command(f'{cd_cmd} && {build_cmd}')
        if not built:
            return built

        return VoidResult()

    def generate(self) -> VoidResult:
        return VoidResult()

    def install(self, version, installation_dir=None) -> VoidResult:
        if exists(self.compiler):
            return VoidResult()

        if not installation_dir:
            installation_dir = self.output_file + "/java-compiler/"

        path = "https://github.com/adoptium/temurin8-binaries/releases/download/"
        match = re.search(fr'(\d{{1,2}})u(.*)', version)

        jdk_version = match.groups()[0]
        jdk_hash = match.groups()[1]
        platform = "x64_linux"

        file_to_download = f'OpenJDK{jdk_version}U-jdk_{platform}_hotspot_{version.replace("-", "")}.tar.gz'
        path += f'jdk{version}/{file_to_download}'

        file_to_download = f'{self.output_file}/{file_to_download}'

        if not exists(file_to_download):
            LOG_DEBUG(f'Downloading compiler source: {file_to_download}')
            downloaded = download_file(path, file_to_download)
            if not downloaded:
                return downloaded

        LOG_DEBUG(f'Extracting compiler source: {installation_dir}')
        create_dir(installation_dir)
        extract_cmd = f'tar -xzf {file_to_download} -C {installation_dir} --strip-components=1'
        extracted = run_command(extract_cmd)
        if not extracted:
            return extracted

        return VoidResult()