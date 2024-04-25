import os

from engines.fmi2.generator_fmi2 import *
from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf, file_system

output_dir = os.getcwd() + "/generated/"

def main():
    start_logger(LogLevel.DEBUG)
    config = JsonConfiguration()
    config.parse("fmi2_config.json")

    generator = None
    output_name = None
    if not config.has(KEY_SERVER):
        LOG_ERROR("No engine provided")
        return

    file_system.create_dir(output_dir)
    if config[KEY_SERVER] == ENGINE_FMI2:
        generator = ServerGeneratorFMI2(output_dir + ENGINE_FMI2)
    else:
        LOG_ERROR(f'Unknown engine {config[KEY_SERVER]}')
        return

    result = protobuf.generate_python(output_dir)
    if not result.is_success():
        LOG_ERROR(result)
        return

    if generator:
        generated = generator.generate(config)
        if not generated:
            LOG_ERROR(f'Failed to generate server: {generated}')

if __name__ == '__main__':
    main()