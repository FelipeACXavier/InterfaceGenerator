import os

from engines.hla_rti1516.generator_hla import *
from engines.fmi2.generator_fmi2 import *
from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf, git, file_system
from tools.compilers import cmake, javac

output_dir = os.getcwd() + "/generated/"
rti_dir = output_dir + "/OpenRTI/"

def create_cmake_compiler(output_dir):
    compiler = cmake.CMakeCompiler(output_dir)

    compiler.add_version("3.5.1")

    compiler.set_project("hla")
    compiler.add_option("-O1")
    compiler.add_option("-Wno-deprecated")

    compiler.add_source("main.cpp")
    compiler.add_source("*.cpp")
    compiler.add_source("dtig/*.cc")

    compiler.add_include_dir(output_dir, relative=False)
    compiler.add_include_dir(f'{rti_dir}/install/include/rti1516', relative=False)

    compiler.add_library_dir(f'{rti_dir}/install/lib', relative=False)

    compiler.add_library("rti1516 fedtime1516")
    compiler.add_library("protobuf")
    compiler.add_library("pthread")

    return compiler


def main():
    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("config.json")

    compiler = None
    server_generator = None
    client_generator = None

    server_name = None
    client_name = None

    if not config.has(KEY_CLIENT):
        LOG_ERROR("No client provided")
        return

    if config[KEY_CLIENT] == ENGINE_HLA_RTI1516:
        if not config.has(KEY_SERVER):
            LOG_ERROR("The HLA client requires a coupled server")
            return

        create_dir(output_dir)

        # Make sure the OpenRTI library is available
        if not os.path.isdir(rti_dir):
            cloned = git.Git("https://github.com/onox/OpenRTI.git").clone(rti_dir)
            if not cloned:
                LOG_ERROR(cloned)
                return

        # Compile OpenRTI
        rtiCompiler = cmake.CMakeCompiler(rti_dir)
        compiled = rtiCompiler.compile(["install"])
        if not compiled:
            LOG_ERROR(compiled)
            return

        client_name = ENGINE_HLA_RTI1516
        client_generator = ClientGeneratorRTI1516(output_dir + client_name)

        # Generate protobuf for C++
        result = protobuf.generate_cpp(output_dir)
        if not result:
            LOG_ERROR(result)
            return

        compiler = create_cmake_compiler(output_dir)
    else:
        LOG_ERROR(f'Unknown client {config[KEY_CLIENT]}')
        return

    if config[KEY_SERVER] == ENGINE_FMI2:
        from engines.fmi2.generator_fmi2 import ServerGeneratorFMI2

        server_name = ENGINE_FMI2
        server_generator = ServerGeneratorFMI2(output_dir + server_name)

        # Generate protobuf for python
        result = protobuf.generate_python(output_dir)
        if not result.is_success():
            LOG_ERROR(result)
            return

        client_generator.set_client_info("python", server_generator.get_output_file())

    elif config[KEY_SERVER] == ENGINE_MATLAB_2023b:
        # Engine specific import
        from engines.matlab2023b.generator_matlab2023b import ServerGeneratorMatlab2023b

        server_name = ENGINE_MATLAB_2023b
        server_generator = ServerGeneratorMatlab2023b(output_dir + server_name)

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

        # client_generator.set_client_info("python", server_generator.get_output_file())

    if server_generator:
        server_result = server_generator.generate(config)
        if not server_result.is_success():
            LOG_ERROR(f'Failed to generate server: {server_result}')

    if client_generator:
        client_result = client_generator.generate(config)
        if not client_result.is_success():
            LOG_ERROR(f'Failed to generate client: {client_result}')

    if compiler:
        generated = compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated compiler file: {generated}')

        compiled = compiler.compile()
        if not compiled:
            LOG_ERROR(f'Failed to compile file: {compiled}')

if __name__ == '__main__':
    main()