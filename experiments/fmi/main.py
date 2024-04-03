import os

from engines.fmi2.generator_fmi2 import *
from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf

def main():
    start_logger(LogLevel.TRACE)
    config = JsonConfiguration()
    config.parse("config.json")

    server_generator = None
    client_generator = None
    output_name = None
    if not config.has(KEY_SERVER):
        LOG_ERROR("No target provided")
        return

    output_dir = os.getcwd() + "/build/"

    if config[KEY_SERVER] == ENGINE_FMI2:
        server_generator = ServerGeneratorFMI2(output_dir + ENGINE_FMI2)
    else:
        LOG_ERROR(f'Unknown target {config[KEY_SERVER]}')
        return

    try:
        os.mkdir(output_dir)
    except FileExistsError as e:
        pass

    result = protobuf.generate_python(output_dir)
    if not result.is_success():
        LOG_ERROR(result)
        return

    if server_generator:
        server_result = server_generator.generate(config)
        if not server_result.is_success():
            LOG_ERROR(f'Failed to generate server: {server_result}')

if __name__ == '__main__':
    main()