import os

from dtig.engines.fmi2.generator_fmi2 import *
from dtig.common.json_configuration import JsonConfiguration

from dtig.common.keys import *
from dtig.common.engines import *
from dtig.common.logging import *

from dtig.tools import protobuf

def main():
    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("config.json")

    server_generator = None
    client_generator = None
    output_name = None
    if not config.has(KEY_TARGET):
        LOG_ERROR("No target provided")
        return

    if config[KEY_TARGET] == ENGINE_FMI2:
        server_generator = ServerGeneratorFMI2()
        client_generator = ClientGeneratorFMI2()
        output_name = ENGINE_FMI2
    else:
        LOG_ERROR(f'Unknown target {config[KEY_TARGET]}')
        return

    output_dir = os.getcwd() + "/build/"
    try:
        os.mkdir(output_dir)
    except FileExistsError as e:
        pass

    result = protobuf.install_protoc()
    if not result.is_success():
        LOG_ERROR(result)
        return

    protobuf.generate_python(output_dir)

    if server_generator:
        server_result = server_generator.generate(output_dir + output_name, config)
        if not server_result.is_success():
            LOG_ERROR(f'Failed to generate server: {server_result}')

    if client_generator:
        client_result = client_generator.generate(output_dir + output_name, config)
        if not client_result.is_success():
            LOG_ERROR(f'Failed to generate client: {client_result}')

if __name__ == '__main__':
    main()