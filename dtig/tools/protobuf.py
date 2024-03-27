import os
import subprocess

from dtig.common.logging import *
from dtig.tools.file_system import *
from dtig.common.result import VoidResult

ENV_DIR = os.environ['VIRTUAL_ENV'] + "/"
BIN_DIR = ENV_DIR + "bin/"
INCLUDE_DIR = ENV_DIR + "include/"
ROOT_DIR = ENV_DIR + "../"
PROTOC = BIN_DIR + "protoc"
PROTOBUF_DIR = ROOT_DIR + "protobuf"


def protobuf_generator(func):
    def wrapper_func(*args, **kwargs):
        LOG_DEBUG(f'Generating protos at {args[0]}')
        result = func(*args, **kwargs)
        if result.returncode != 0:
            return VoidResult.failed(f'Failed to generate protobuf: {result.stderr}')
        return VoidResult()

    return wrapper_func

@protobuf_generator
def generate_python(out_dir : str):
    command = f'{PROTOC} -I={ROOT_DIR} --python_out={out_dir} {PROTOBUF_DIR}/*.proto'
    return subprocess.run(command, shell=True)

def install_protoc() -> VoidResult:
    if os.path.isfile(PROTOC):
        return VoidResult()

    LOG_DEBUG('protoc is not installed downloading it now')

    protoc_zip = ROOT_DIR + "protoc.zip"
    protoc_dir = ROOT_DIR + "protoc"

    # TODO: Make it configurable
    url = (
        "https://github.com/protocolbuffers/protobuf/releases/download/v26.0/"
        "protoc-26.0-linux-x86_64.zip"
    )

    download = download_file(url, protoc_zip)
    if not download.is_success():
        return download

    extraction = extract_archive(protoc_zip, protoc_dir)
    if not extraction.is_success():
        return extraction

    # Copy the downloaded files to the virtual environment
    cp_bin = copy_archive(protoc_dir + "/bin", BIN_DIR)
    if not cp_bin.is_success():
        return cp_bin

    cp_include = copy_archive(protoc_dir + "/include", INCLUDE_DIR)
    if not cp_include.is_success():
        return cp_include

    # Clean up enviroment
    shutil.rmtree(protoc_zip, ignore_errors=True)
    shutil.rmtree(protoc_dir, ignore_errors=True)

    return VoidResult()


