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
    compiler.add_source(f'{output_dir}/dtig/*.cc', relative=False)

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
    config.parse("hla_config.json")

    compiler = None
    generator = None

    if not config.has(KEY_ENGINE):
        LOG_ERROR("No engine provided")
        return

    file_system.create_dir(output_dir)
    if config[KEY_ENGINE] == ENGINE_HLA_RTI1516:
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

        generated_file_name = ENGINE_HLA_RTI1516
        generator = ClientGeneratorRTI1516(output_dir + generated_file_name)

        # Generate protobuf for C++
        result = protobuf.generate_cpp(output_dir)
        if not result:
            LOG_ERROR(result)
            return

        compiler = create_cmake_compiler(output_dir)
    else:
        LOG_ERROR(f'Unknown engine {config[KEY_ENGINE]}')
        return

    if generator:
        generated = generator.generate(config)
        if not generated.is_success():
            LOG_ERROR(f'Failed to generate client: {generated}')

    if compiler:
        generated = compiler.generate()
        if not generated:
            LOG_ERROR(f'Failed to generated compiler file: {generated}')

        compiled = compiler.compile()
        if not compiled:
            LOG_ERROR(f'Failed to compile file: {compiled}')

if __name__ == '__main__':
    main()