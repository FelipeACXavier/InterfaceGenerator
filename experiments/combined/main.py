import argparse

from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf, git, file_system
from tools.compilers import cmake, javac

argument_parser = argparse.ArgumentParser(description='DTIG generator')
argument_parser.add_argument('-c', action="store", dest="config_file", help='Configuration file to use', type=str)
argument_parser.add_argument('-l', action="store", dest="log_level", help='Desired log level', type=int, default=int(LogLevel.DEBUG))
argument_parser.add_argument('-g', action="store_false", dest="compile", help='Only generate files', default=True)
argument_parser.add_argument('--proto', action="store_true", dest="compile_proto", help='Compile protobuf files', default=False)
argument_parser.add_argument('--client', action="store_true", dest="no_server", help='Only generate the client', default=False)
argument_parser.add_argument('--server', action="store_true", dest="no_client", help='Only generate the server', default=False)
args = argument_parser.parse_args()

def create_cmake_compiler(server_name, output_dir, rti_dir):
    compiler = cmake.CMakeCompiler(output_dir)

    compiler.add_version("3.5.1")

    compiler.set_project(f"{server_name}_hla")
    compiler.add_option("-O1")
    compiler.add_option("-Wno-deprecated")

    compiler.add_source("main.cpp")
    compiler.add_source("*.cpp")
    compiler.add_source(f'{output_dir}/dtig/*.cc', relative=False)

    compiler.add_include_dir(output_dir, relative=False)
    compiler.add_include_dir(f'{rti_dir}/install/include/rti1516', relative=False)

    compiler.add_library_dir(f'{rti_dir}/install/lib', relative=False)

    compiler.add_library("rti1516 fedtime1516")
    compiler.add_library("protobuf")
    compiler.add_library("pthread")

    return compiler

def main():
    start_logger(LogLevel(args.log_level))
    output_dir = file_system.current_dir() + "/generated/"

    if not args.config_file:
        LOG_ERROR("No configuration file provided")
        return

    LOG_INFO(f'Using configuration: {args.config_file}')
    config = JsonConfiguration()
    config.parse(args.config_file)

    if not config.has(KEY_SERVER):
        LOG_ERROR("No server provided")
        return

    if not config.has(KEY_CLIENT):
        LOG_ERROR("No client provided")
        return

    generator = None
    compiler = None

    server_output_dir = output_dir + f"/{config[KEY_SERVER]}/"
    file_system.create_dir(server_output_dir)
    if args.no_client:
        pass
    elif config[KEY_CLIENT] == ENGINE_HLA_RTI1516:
        from engines.hla_rti1516.generator_hla import ClientGeneratorRTI1516

        # Update output dir
        rti_dir = output_dir + "/OpenRTI/"
        file_system.create_dir(server_output_dir)

        # Make sure the OpenRTI library is available
        if not file_system.exists(rti_dir):
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

        generator = ClientGeneratorRTI1516(f'{server_output_dir}{config[KEY_CLIENT]}')

        # Generate protobuf for C++
        if args.compile_proto:
            result = protobuf.generate_cpp(server_output_dir)
            if not result:
                LOG_ERROR(result)
                return

        compiler = create_cmake_compiler(config[KEY_SERVER], server_output_dir, rti_dir)
    else:
        LOG_ERROR(f'Unknown server: {config[KEY_SERVER]}')
        return

    if generator:
        generated = generator.generate(config)
        if not generated.is_success():
            LOG_ERROR(f'Failed to generate server: {generated}')
            return

    if compiler and args.compile:
        generated = compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated compiler file for server: {generated}')
            return

        compiled = compiler.compile()
        if not compiled:
            LOG_ERROR(f'Failed to compile server file: {compiled}')
            return

    # No server >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    if args.no_server:
        pass
    # No server <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # FMI2 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    elif config[KEY_SERVER] == ENGINE_FMI2:
        from engines.fmi2.generator_fmi2 import ServerGeneratorFMI2
        generator = ServerGeneratorFMI2(server_output_dir + config[KEY_SERVER])

        # Ensure python protos are available
        generated = protobuf.generate_python(server_output_dir)
        if not generated:
            LOG_ERROR(result)
            return

        generated = generator.generate(config)
        if not generated:
            LOG_ERROR(f'Failed to generate FMI server: {generated}')
            return
    # FMI2 <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Matlab >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    elif config[KEY_SERVER] == ENGINE_MATLAB_2024a or config[KEY_SERVER] == ENGINE_SIMULINK_2024a:
        # Engine specific import
        if config[KEY_SERVER] == ENGINE_MATLAB_2024a:
            from engines.matlab2024a.generator_matlab2024a import ServerGeneratorMatlab2024a
            generator = ServerGeneratorMatlab2024a(server_output_dir + config[KEY_SERVER])
        else:
            from engines.matlab2024a.generator_simulink2024a import ServerGeneratorSimulink2024a
            generator = ServerGeneratorSimulink2024a(server_output_dir + config[KEY_SERVER])

        # Generate protobuf for matlab
        result = protobuf.generate_matlab(server_output_dir)
        if not result.is_success():
            LOG_ERROR(result)
            return

        java_compiler = javac.JavaCompiler(server_output_dir)
        java_compiler.set_compiler(f'{server_output_dir}/java-compiler/bin/javac')
        java_compiler.add_source("dtig/*.java")
        java_compiler.add_library_dir("protobuf-java-3.20.3.jar")

        generated = java_compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated java compiler file: {generated}')
            return

        installed = java_compiler.install("8u402-b06")
        if not installed:
            LOG_ERROR(f'Failed to install java compiler: {installed}')
            return

        compiled = java_compiler.compile()
        if not compiled:
            LOG_ERROR(f'Javac failed to compile file: {compiled}')
            return

        # Generate the actual matlab server
        generated = generator.generate(config)
        if not generated:
            LOG_ERROR(f'Failed to generate server: {generated}')
            return

    # Matlab <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # FreeCAD >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    elif config[KEY_SERVER] == ENGINE_FREECAD_021:
        from engines.freecad.generator_freecad import ServerGeneratorFreeCAD
        generator = ServerGeneratorFreeCAD(server_output_dir + ENGINE_FREECAD_021)

        # Ensure python protos are available
        generated = protobuf.generate_python(server_output_dir)
        if not generated:
            LOG_ERROR(result)
            return

        generated = generator.generate(config)
        if not generated:
            LOG_ERROR(f'Failed to generate FreeCAD server: {generated}')
            return
    # FreeCAD <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    else:
        LOG_ERROR(f'Unknown engine {config[KEY_SERVER]}')
        return

if __name__ == '__main__':
    main()