import os
import subprocess

from dtig.common.logging import *
from dtig.tools.file_system import *
from dtig.common.result import VoidResult

ENV_DIR = os.environ['VIRTUAL_ENV'] + "/"
ROOT_DIR = ENV_DIR + "../"
BIN_DIR = ENV_DIR + "bin/"
INCLUDE_DIR = ENV_DIR + "include/"
LIB_DIR = ENV_DIR + "lib"

PROTOC = BIN_DIR + "protoc"
PROTOBUF_DIR = ROOT_DIR + "protobuf"
LD_LIBRARY_PATH="LD_LIBRARY_PATH"

# Generic commands for all generators
def protobuf_generator(func):
    def wrapper_func(*args, **kwargs):
        LOG_TRACE(f'Generating protos at {args[0]}')

        # Before any generation, make sure that we have the necessary binaries installed
        installed = install_protoc()
        if not installed:
            return installed

        return func(*args, **kwargs)

    return wrapper_func

@protobuf_generator
def generate_python(out_dir : str):
    command = f'{PROTOC} -I={ROOT_DIR} --python_out={out_dir} {PROTOBUF_DIR}/*.proto'
    return run_command(command)

@protobuf_generator
def generate_cpp(out_dir : str):
    # Cpp is annoying, so make sure that the library path is recognized
    updated_lib = run_command(f'export {LD_LIBRARY_PATH}=${LD_LIBRARY_PATH}:{LIB_DIR}')
    if not updated_lib:
        return updated_lib

    command = f'{PROTOC} -I={ROOT_DIR} --cpp_out={out_dir} {PROTOBUF_DIR}/*.proto'
    return run_command(command)


def install_protoc(force_install : bool = False) -> VoidResult:
    # It is useful to force a reinstallation in case of a new version for example
    if not force_install and os.path.isfile(PROTOC):
        return VoidResult()

    # Make it configurable
    repo_dir = ROOT_DIR + "tmp_protobuf_repo"
    url = "https://github.com/protocolbuffers/protobuf/"
    version = "v3.20.3"

    if not os.path.isdir(repo_dir):
        cloned = run_command(f'git clone --depth 1 --recurse-submodules --shallow-submodules --branch {version} {url} {repo_dir}')
        if not cloned:
            return cloned

    cd_cmd = f'cd {repo_dir}'
    cmake_cmd = f'./autogen.sh && ./configure --prefix={ENV_DIR} && make -j4 && make install'
    built = run_command(f'{cd_cmd} && {cmake_cmd}')
    if not built:
        return built

    # shutil.rmtree(repo_dir, ignore_errors=True)

    return VoidResult()
