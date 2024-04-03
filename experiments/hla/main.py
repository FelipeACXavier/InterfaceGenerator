import os

from engines.hla_rti1516.generator_hla import *
from engines.fmi2.generator_fmi2 import *
from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf
from tools.compilers import cmake

output_dir = os.getcwd() + "/generated/"

def create_cmake_compiler(output_dir):
    compiler = cmake.CMakeCompiler(output_dir)

    compiler.add_version("3.5.1")

    compiler.add_source("main.cpp")
    compiler.add_source("*.cpp")
    compiler.add_source("dtig/*.cc")

    compiler.add_include_dir(output_dir, relative=False)
    compiler.add_include_dir("/install/include/rti1516")

    compiler.add_library_dir("/install/lib")

    compiler.add_library("libcpphelpers")
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
        client_name = ENGINE_HLA_RTI1516
        client_generator = ClientGeneratorRTI1516(output_dir + client_name)

        # Generate protobuf for C++
        result = protobuf.generate_cpp(output_dir)
        if not result:
            LOG_ERROR(result)
            return

        compiler = create_cmake_compiler(output_dir)

        base_compiler = cmake.CMakeCompiler(output_dir + "../")
        base_compiler.add_version("3.5.1")
        base_compiler.set_project("hla")

        base_compiler.add_option("-O1")
        base_compiler.add_option("-Wno-deprecated")

        base_compiler.add_subfolder("CppHelpers")
        base_compiler.add_subfolder("generated")

        base_compiler.generate()

        # The HLA client requires a coupled server
        if config[KEY_SERVER] == ENGINE_FMI2:
            server_name = ENGINE_FMI2
            server_generator = ServerGeneratorFMI2(output_dir + server_name)

            # Generate protobuf for python
            result = protobuf.generate_python(output_dir)
            if not result.is_success():
                LOG_ERROR(result)
                return

            client_generator.set_client_info("python", server_generator.get_output_file())
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

    if client_generator:
        client_result = client_generator.generate(config)
        if not client_result.is_success():
            LOG_ERROR(f'Failed to generate client: {client_result}')

    if compiler:
        generated = compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated compiler file: {generated}')

        # compiled = compiler.compile()
        # if not compiled:
        #     LOG_ERROR(f'Failed to compile file: {compiled}')

if __name__ == '__main__':
    main()