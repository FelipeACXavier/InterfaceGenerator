import os
import subprocess

from common.logging import *
from tools.file_system import *
from common.result import VoidResult

ENV_DIR = os.environ['VIRTUAL_ENV'] + "/"
ROOT_DIR = ENV_DIR + "../"
BIN_DIR = ENV_DIR + "bin/"
INCLUDE_DIR = ENV_DIR + "include/"
LIB_DIR = ENV_DIR + "lib"

PROTOBUF_VERSION="3.20.3"
PROTOC = BIN_DIR + "protoc"
PROTOBUF_DIR = ROOT_DIR + "protobuf/"
PROTOBUF_DTIG_DIR = PROTOBUF_DIR + "dtig"
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
    command = f'{PROTOC} -I={PROTOBUF_DIR} --python_out={out_dir} {PROTOBUF_DTIG_DIR}/*.proto'
    return run_command(command)

@protobuf_generator
def generate_cpp(out_dir : str):
    command = f'{PROTOC} -I={PROTOBUF_DIR} --cpp_out={out_dir} {PROTOBUF_DTIG_DIR}/*.proto'
    return run_command(command)

@protobuf_generator
def generate_java(out_dir : str):
    # Check if library is available
    jar_file = f'protobuf-java-{PROTOBUF_VERSION}.jar'
    url = f'https://repo1.maven.org/maven2/com/google/protobuf/protobuf-java/{PROTOBUF_VERSION}/{jar_file}'
    file_to_download = out_dir + f'/{jar_file}'

    if not exists(file_to_download):
        downloaded = download_file(url, file_to_download)
        if not downloaded:
            return downloaded

    command = f'{PROTOC} -I={PROTOBUF_DIR} --java_out={out_dir} {PROTOBUF_DTIG_DIR}/*.proto'
    return run_command(command)

def generate_matlab(out_dir : str):
    # Matlab uses the java protobuf but they must be compiled with a specific javac version
    return generate_java(out_dir)

def install_protoc(force_install : bool = False) -> VoidResult:
    # It is useful to force a reinstallation in case of a new version for example
    if not force_install and os.path.isfile(PROTOC):
        return VoidResult()

    # Make it configurable
    repo_dir = ROOT_DIR + "tmp_protobuf_repo"
    url = "https://github.com/protocolbuffers/protobuf/"
    version = f'v{PROTOBUF_VERSION}'

    if not os.path.isdir(repo_dir):
        cloned = git.Git(url).clone(repo_dir, branch=version)
        if not cloned:
            return cloned

    cd_cmd = f'cd {repo_dir}'
    cmake_cmd = f'./autogen.sh && ./configure --prefix={ENV_DIR} && make -j4 && make install'
    built = run_command(f'{cd_cmd} && {cmake_cmd}')
    if not built:
        return built

    # shutil.rmtree(repo_dir, ignore_errors=True)

    return VoidResult()
