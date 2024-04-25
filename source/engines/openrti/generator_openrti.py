from interface.cpp_generator import HppGenerator, CppGenerator

class HppGeneratorOpenRTI(HppGenerator):
    def __init__(self, output_file):
        super().__init__(output_file)

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: variable_type
        dtig_parser.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)

class CppGeneratorOpenRTI(CppGenerator):
    def __init__(self, output_file, header_name = None):
        super().__init__(output_file, header_name)

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        return super().generate(config)

    def parse_dtig_language(self, parser=None):
        from language import parser

        dtig_parser = parser.Parser(self.config)

        # Define callbacks
        dtig_parser.type_to_function = lambda variable_type: cpp.to_type(variable_type)
        dtig_parser.to_proto_message = lambda variable_type: cpp.to_proto_message(variable_type)
        dtig_parser.to_string = lambda variable_type: f'\"{variable_type}\"'

        return super().parse_dtig_language(parser=dtig_parser)