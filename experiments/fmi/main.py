import os

from dtig.engines.fmi import generator_fmi2
from dtig.common.json_configuration import JsonConfiguration

from dtig.common.keys import *
from dtig.common.engines import *
from dtig.common.logging import *

def main():
    config = JsonConfiguration()
    config.parse("config.json")

    server_generator = None
    client_generator = None
    output_name = None
    if not config.has(KEY_TARGET):
        LOG_ERROR("No target provided")
        return

    if config[KEY_TARGET] == ENGINE_FMI2:
        server_generator = generator_fmi2.ServerGeneratorFMI2()
        client_generator = generator_fmi2.ClientGeneratorFMI2()
        output_name = ENGINE_FMI2
    else:
        LOG_ERROR(f'Unknown target {config[KEY_TARGET]}')
        return

    output_dir = "build/"
    try:
        os.mkdir(output_dir)
    except FileExistsError as e:
        pass

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