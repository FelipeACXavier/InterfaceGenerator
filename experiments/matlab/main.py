import os

from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf, file_system
from tools.compilers import javac

output_dir = os.getcwd() + "/generated/"

def main():
    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("config.json")

    generator = None
    output_name = None

    if not config.has(KEY_ENGINE):
        LOG_ERROR("No engine provided")
        return

    file_system.create_dir(output_dir)
    if config[KEY_ENGINE] == ENGINE_MATLAB_2024a:
        # Engine specific import
        from engines.matlab2024a.generator_matlab2024a import ServerGeneratorMatlab2024a
        from engines.matlab2024a.generator_simulink2024a import ServerGeneratorSimulink2024a

        # generator = ServerGeneratorMatlab2024a(output_dir + ENGINE_MATLAB_2024a)
        generator = ServerGeneratorSimulink2024a(output_dir + ENGINE_MATLAB_2024a)

        # Generate protobuf for matlab
        result = protobuf.generate_matlab(output_dir)
        if not result.is_success():
            LOG_ERROR(result)
            return

        java_compiler = javac.JavaCompiler(output_dir)
        java_compiler.set_compiler(f'{output_dir}/java-compiler/bin/javac')
        java_compiler.add_source("dtig/*.java")
        java_compiler.add_library_dir("protobuf-java-3.20.3.jar")

        generated = java_compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated java compiler file: {generated}')

        installed = java_compiler.install("8u402-b06")
        if not installed:
            LOG_ERROR(f'Failed to install java compiler: {installed}')

        compiled = java_compiler.compile()
        if not compiled:
            LOG_ERROR(f'Javac failed to compile file: {compiled}')

    else:
        LOG_ERROR(f'Unknown engine {config[KEY_ENGINE]}')
        return

    if generator:
        generated = generator.generate(config)
        if not generated:
            LOG_ERROR(f'Failed to generate server: {generated}')

if __name__ == '__main__':
    main()