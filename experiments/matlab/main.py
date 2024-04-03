import os

from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf
from tools.compilers import javac

output_dir = os.getcwd() + "/generated/"

def main():
    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("config.json")

    compiler = None
    server_name = None
    server_generator = None

    if config[KEY_SERVER] == ENGINE_MATLAB_2023b:
        # Engine specific import
        from engines.matlab2023b.generator_matlab2023b import ServerGeneratorMatlab2023b

        server_name = ENGINE_MATLAB_2023b
        server_generator = ServerGeneratorMatlab2023b(output_dir + server_name)

        # Generate protobuf for matlab
        result = protobuf.generate_matlab(output_dir)
        if not result.is_success():
            LOG_ERROR(result)
            return

        compiler = javac.JavaCompiler(output_dir)
        compiler.set_compiler(f'{output_dir}/java-compiler/bin/javac')
        compiler.add_source("dtig/*.java")
        compiler.add_library_dir("protobuf-java-3.20.3.jar")

    else:
        LOG_ERROR(f'Unknown client {config[KEY_CLIENT]}')
        return

    try:
        os.mkdir(output_dir)
    except FileExistsError as e:
        pass

    if server_generator:
        server_result = server_generator.generate(config)
        if not server_result.is_success():
            LOG_ERROR(f'Failed to generate server: {server_result}')

    if compiler:
        generated = compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated compiler file: {generated}')

        installed = compiler.install("8u402-b06")
        if not installed:
            LOG_ERROR(f'Failed to install compiler: {installed}')

        compiled = compiler.compile()
        if not compiled:
            LOG_ERROR(f'Failed to compile file: {compiled}')

if __name__ == '__main__':
    main()