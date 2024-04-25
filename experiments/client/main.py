import os
import argparse

from engines.cmd.cmd_generator import *
from common.json_configuration import JsonConfiguration

from common.keys import *
from common.engines import *
from common.logging import *

from tools import protobuf, file_system

output_dir = file_system.current_dir() + "/generated/"
argument_parser = argparse.ArgumentParser(description='DTIG generator')
argument_parser.add_argument('-c', action="store", dest="config_file", help='Configuration file to use', type=str)
argument_parser.add_argument('-l', action="store", dest="log_level", help='Desired log level', type=int, default=int(LogLevel.DEBUG))
args = argument_parser.parse_args()

def main():
    start_logger(LogLevel(args.log_level))

    if not args.config_file:
        LOG_ERROR("No configuration file provided")
        return

    LOG_INFO(f'Using configuration: {args.config_file}')
    config = JsonConfiguration()
    config.parse(file_system.to_absolute_path(args.config_file))

    generator = None
    output_name = None
    if not config.has(KEY_CLIENT):
        LOG_ERROR("No engine provided")
        return

    file_system.create_dir(output_dir)
    generator = ClientGeneratorCMD(output_dir + "client")

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