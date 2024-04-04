import os
import re

from pathlib import Path

from common.keys import *
from common.result import *
from common.logging import *

from tools.file_system import create_dir
from common.model_configuration_base import ModelConfigurationBase

from interface.cpp_generator import HppGenerator, CppGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__) + "/templates"

PARAMETER_HANDLER = "mAttributeHandler"
INPUT_HANDLER = "mInputHandler"
OUTPUT_HANDLER = "mOutputHandler"

class ClientGeneratorRTI1516():
    def __init__(self, output_file):
        template_dir = f'{Path(output_file).parent.absolute()}/templates'
        create_dir(template_dir)

        self.federate_h_callbacks = f'{template_dir}/federate_callbacks.h'
        self.federate_cpp_callbacks = f'{template_dir}/federate_callbacks.cpp'

        self.server_cmd = None
        self.server_path = None

        self.output_file = output_file

    def generate(self, config : ModelConfigurationBase) -> VoidResult:
        self.config = config
        self.generate_model_config()

        # Output file names
        federate_header = self.output_file + "_federate.h"
        federate_source = self.output_file + "_federate.cpp"

        ambassador_header = self.output_file + "_ambassador.h"
        ambassador_source = self.output_file + "_ambassador.cpp"

        # Federate generators
        federate_hpp = HppGenerator(federate_header)
        federate_hpp.engine_template_file = self.federate_h_callbacks
        federate_hpp.common_template_file = engine_folder + "/federate_template.h"

        federate_cpp = CppGenerator(federate_source, Path(federate_header).name)
        federate_cpp.engine_template_file = self.federate_cpp_callbacks
        federate_cpp.common_template_file = engine_folder + "/federate_template.cpp"

        federate_cpp.new_callback("server_cmd", self.server_cmd)
        federate_cpp.new_callback("server_path", self.server_path)

        # Ambassador generators
        ambassador_hpp = HppGenerator(ambassador_header)
        ambassador_hpp.common_template_file = engine_folder + "/ambassador_template.h"

        ambassador_cpp = CppGenerator(ambassador_source, Path(ambassador_header).name)
        ambassador_cpp.common_template_file = engine_folder + "/ambassador_template.cpp"

        # =======================================================================================
        # Begin generation
        # First the ambassador
        generated = ambassador_hpp.generate(config)
        if not generated:
            return generated

        generated = ambassador_cpp.generate(config)
        if not generated:
            return generated

        # Then the federate
        # Make the ambassador configuration available to the federate
        ambassador_name = ambassador_hpp.callbacks[KEY_CLASS_NAME]
        federate_hpp.new_callback("ambassador", ambassador_name)
        federate_hpp.new_callback("ambassador_header", {KEY_NAME: None, KEY_BODY: Path(ambassador_header).name, KEY_SELF: False})
        federate_cpp.new_callback("ambassador", ambassador_name)
        federate_cpp.new_callback("ambassador_header", {KEY_NAME: None, KEY_BODY: Path(ambassador_header).name, KEY_SELF: False})

        generated = federate_hpp.generate(config)
        if not generated:
            return generated

        generated = federate_cpp.generate(config)
        if not generated:
            return generated

        return VoidResult()

    def set_client_info(self, server_cmd, server_path):
        self.server_cmd  = {KEY_NAME: None, KEY_BODY: server_cmd,  KEY_SELF: False}
        self.server_path = {KEY_NAME: None, KEY_BODY: server_path, KEY_SELF: False}

    def generate_model_config(self):
        h_body = ""
        cpp_body = ""

        h, cpp = self.generate_model_members()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_set_input()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_get_output()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_set_parameter()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_get_parameter()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_subscriptions()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_publications()
        h_body += h
        cpp_body += cpp

        with open(self.federate_h_callbacks, "w") as f:
            f.write(h_body)

        with open(self.federate_cpp_callbacks, "w") as f:
            f.write(cpp_body)

    def generate_model_members(self) -> str:
        h_body = f'// @callback({KEY_INITIALIZE})\n'
        h_body += "void initializeHandles();\n"

        cpp_body = f'// @callback({KEY_INITIALIZE})\n'
        cpp_body += "void initializeHandles()\n{\n"
        cpp_body += "\ttry\n"
        cpp_body += "\t{\n"

        h_body += f'\n// @{KEY_MEMBER}(private)\n'
        h, cpp = self.generate_model_parameters()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_inputs()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_outputs()
        h_body += h
        cpp_body += cpp

        cpp_body += "\t}\n"
        cpp_body += "\tcatch (NameNotFound error)\n"
        cpp_body += "\t{\n"
        cpp_body += '\t\tstd::wcout << "Failed to initialize handles: " << error.what() << std::endl;\n'
        cpp_body += "\t}\n"
        cpp_body += "}\n"

        return h_body, cpp_body

    def generate_model_inputs(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has(KEY_INPUTS):
            h_body += f'rti1516::InteractionClassHandle {INPUT_HANDLER};\n'
            h_body += f'std::map<rti1516::ParameterHandle, std::string> {INPUT_HANDLER}s;\n'

            cpp_body += f'\t\t{INPUT_HANDLER} = rtiamb->getInteractionClassHandle(L"{self.config[KEY_INPUTS][0][KEY_NAMESPACE]}");\n'

            for item in self.config[KEY_INPUTS]:
                cpp_body += f'\t\t{INPUT_HANDLER}s.insert({{rtiamb->getParameterHandle({INPUT_HANDLER}, L"{item[KEY_NAME]}"), "{item[KEY_NAME]}"}});\n'

        return h_body, cpp_body

    def generate_model_outputs(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has(KEY_OUTPUTS):
            h_body += f'rti1516::InteractionClassHandle {OUTPUT_HANDLER};\n'
            h_body += f'std::map<std::string, rti1516::ParameterHandle> {OUTPUT_HANDLER}s;\n'

            cpp_body += f'\t\t{OUTPUT_HANDLER} = rtiamb->getInteractionClassHandle(L"{self.config[KEY_OUTPUTS][0][KEY_NAMESPACE]}");\n'

            for item in self.config[KEY_OUTPUTS]:
                cpp_body += f'\t\t{OUTPUT_HANDLER}s.insert({{"{item[KEY_NAME]}", rtiamb->getParameterHandle({OUTPUT_HANDLER}, L"{item[KEY_NAME]}")}});\n'

        return h_body, cpp_body

    def generate_model_parameters(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has(KEY_PARAMETERS):
            h_body += f'rti1516::ObjectClassHandle {PARAMETER_HANDLER};\n'
            h_body += f'std::map<std::string, rti1516::AttributeHandle> {PARAMETER_HANDLER}s;\n'

            cpp_body += f'\t\t{PARAMETER_HANDLER} = rtiamb->getObjectClassHandle(L"{self.config[KEY_PARAMETERS][0][KEY_NAMESPACE]}");\n'
            for item in self.config[KEY_PARAMETERS]:
                cpp_body += f'\t\t{PARAMETER_HANDLER}s.insert({{"{item[KEY_NAME]}", rtiamb->getAttributeHandle({PARAMETER_HANDLER}, L"{item[KEY_NAME]}")}});\n'

        return h_body, cpp_body

    def generate_model_set_input(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_INPUTS):
            return h_body, cpp_body

        h_body = f'\n// @callback({KEY_SET_INPUT})\n'
        h_body += "void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues);\n"

        cpp_body = f'\n// @callback({KEY_SET_INPUT})\n'
        cpp_body += "void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues)\n{\n"
        cpp_body += "\tdtig::MInput inputMessage;\n"

        cpp_body += "\tfor (auto i = parameterValues.begin(); i != parameterValues.end(); ++i)\n"
        cpp_body += "\t{\n"
        cpp_body += "\t\tstd::string item = mInputHandlers[i->first];\n"
        cpp_body += "\t\tinputMessage.mutable_inputs()->mutable_identifiers()->mutable_names()->add_names(item);\n"
        for i, cfg in enumerate(self.config[KEY_INPUTS]):
            cpp_body += f'\t\t{"if" if i == 0 else "else if"} (item == "{cfg[KEY_NAME]}")\n'
            cpp_body += "\t\t{\n"
            if cfg["type"] == "float":
                cpp_body += f'\t\t\tdtig::MF32 value;\n'
            elif cfg["type"] == "double":
                cpp_body += f'\t\t\tdtig::MF64 value;\n'
            elif cfg["type"] == "int32":
                cpp_body += f'\t\t\tdtig::MI32 value;\n'
            elif cfg["type"] == "uint32":
                cpp_body += f'\t\t\tdtig::MU32 value;\n'

            cpp_body += f'\t\t\tvalue.set_value(fromData<{cfg["type"]}>(i->second));\n'
            cpp_body += "\t\t\tinputMessage.mutable_inputs()->add_values()->PackFrom(value);\n"

            cpp_body += "\t\t}\n"

        cpp_body += "\t\telse\n"
        cpp_body += "\t\t{\n"
        cpp_body += '\t\t\tstd::cout << "Unknown input: " << item << std::endl;\n'
        cpp_body += '\t\t\treturn;\n'
        cpp_body += "\t\t}\n"

        cpp_body += "\t}\n\n"

        cpp_body += '\tdtig::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_input() = inputMessage;\n'
        cpp_body += '\tdtig::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dtig::ReturnCode::SUCCESS)\n\t'
        cpp_body += '\tstd::cout << "Failed to set inputs: " << ret.error_message().value() << std::endl;\n'

        cpp_body += '}\n'

        return h_body, cpp_body

    def generate_model_get_output(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_OUTPUTS):
            return h_body, cpp_body

        h_body += f'\n// @callback({KEY_GET_OUTPUT})\n'
        h_body += f'void GetOutput();\n'

        cpp_body += f'\n// @callback({KEY_GET_OUTPUT})\n'
        cpp_body += "void GetOutput()\n{\n"
        cpp_body += "\tdtig::MOutput outputMessage;\n"

        if self.config.has(KEY_OUTPUTS):
            for o in self.config[KEY_OUTPUTS]:
                cpp_body += f'\toutputMessage.mutable_outputs()->mutable_identifiers()->mutable_names()->add_names("{o[KEY_NAME]}");\n'

        cpp_body += '\tdtig::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_output() = outputMessage;\n'
        cpp_body += '\tdtig::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dtig::ReturnCode::SUCCESS)\n\t{\n'
        cpp_body += '\t\tstd::cout << "Failed to get outputs: " << ret.error_message().value() << std::endl;\n'
        cpp_body += '\t\treturn;\n\t}\n\n'

        cpp_body += "\tParameterHandleValueMap parameters;\n"
        for index, o in enumerate(self.config[KEY_OUTPUTS]):
            cpp_body += f'\tstd::string id{o[KEY_NAME]} = ret.values().identifiers().names().names({index});\n'
            if o["type"] == "float":
                cpp_body += f'\tdtig::MF32 value{o[KEY_NAME]};\n'
            elif o["type"] == "double":
                cpp_body += f'\tdtig::MF64 value{o[KEY_NAME]};\n'
            elif o["type"] == "int32":
                cpp_body += f'\tdtig::MI32 value{o[KEY_NAME]};\n'
            elif o["type"] == "uint32":
                cpp_body += f'\tdtig::MU32 value{o[KEY_NAME]};\n'

            cpp_body += f'\tif (ret.values().values({index}).UnpackTo(&value{o[KEY_NAME]}))\n'
            cpp_body += "\t{\n"
            cpp_body += f'\t\t{o["type"]} v{o[KEY_NAME]} = value{o[KEY_NAME]}.value();\n'
            cpp_body += f'\t\tparameters[mOutputHandlers.at(id{o[KEY_NAME]})] = toData<{o["type"]}>(&v{o[KEY_NAME]});\n'
            cpp_body += "\t}\n\n"

        cpp_body += f'\trtiamb->sendInteraction({OUTPUT_HANDLER}, parameters, toVariableLengthData(mName.c_str()));\n'
        cpp_body += "}\n"

        return h_body, cpp_body

    def generate_model_set_parameter(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_PARAMETERS):
            return h_body, cpp_body

        h_body = f'\n// @callback({KEY_SET_PARAMETER})\n'
        h_body += "void SetParameters(const rti1516::ObjectInstanceHandle& object, const rti1516::AttributeHandleValueMap& attributes);\n"

        cpp_body = f'\n// @callback({KEY_SET_PARAMETER})\n'
        cpp_body += "void SetParameters(const rti1516::ObjectInstanceHandle& object, const rti1516::AttributeHandleValueMap& attributes)\n{\n"
        cpp_body += "\tdtig::MParameter paramMessage;\n"

        cpp_body += "\tfor (auto i = attributes.begin(); i != attributes.end(); ++i)\n"
        cpp_body += "\t{\n"
        cpp_body += "\t\tstd::string item;\n"
        cpp_body += f'\t\tfor (auto it = {PARAMETER_HANDLER}s.begin(); it != {PARAMETER_HANDLER}s.end(); ++it)\n'
        cpp_body += f'\t\t\tif (it->second == i->first)\n'
        cpp_body += "\t\t\t{\n"
        cpp_body += "\t\t\t\titem = it->first;\n"
        cpp_body += "\t\t\t\tbreak;\n"
        cpp_body += "\t\t\t}\n\n"

        cpp_body += "\t\tif (item.empty())\n"
        cpp_body += "\t\t\tcontinue;\n\n"

        cpp_body += "\t\tparamMessage.mutable_parameters()->mutable_identifiers()->mutable_names()->add_names(item);\n"
        for i, cfg in enumerate(self.config[KEY_PARAMETERS]):
            cpp_body += f'\t\t{"if" if i == 0 else "else if"} (item == "{cfg[KEY_NAME]}")\n'
            cpp_body += "\t\t{\n"
            if cfg["type"] == "float":
                cpp_body += f'\t\t\tdtig::MF32 value;\n'
            elif cfg["type"] == "double":
                cpp_body += f'\t\t\tdtig::MF64 value;\n'
            elif cfg["type"] == "int32":
                cpp_body += f'\t\t\tdtig::MI32 value;\n'
            elif cfg["type"] == "uint32":
                cpp_body += f'\t\t\tdtig::MU32 value;\n'

            cpp_body += f'\t\t\tvalue.set_value(fromData<{cfg["type"]}>(i->second));\n'
            cpp_body += "\t\t\tparamMessage.mutable_parameters()->add_values()->PackFrom(value);\n"

            cpp_body += "\t\t}\n"

        cpp_body += "\t\telse\n"
        cpp_body += "\t\t{\n"
        cpp_body += '\t\t\tstd::cout << "Unknown input: " << item << std::endl;\n'
        cpp_body += '\t\t\treturn;\n'
        cpp_body += "\t\t}\n"

        cpp_body += "\t}\n\n"

        cpp_body += '\tdtig::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_parameter() = paramMessage;\n'
        cpp_body += '\tdtig::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dtig::ReturnCode::SUCCESS)\n\t'
        cpp_body += '\tstd::cout << "Failed to set parameters: " << ret.error_message().value() << std::endl;\n'

        cpp_body += '}\n'

        return h_body, cpp_body

    def generate_model_get_parameter(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_OUTPUTS):
            return h_body, cpp_body

        h_body += f'\n// @callback({KEY_GET_PARAMETER})\n'
        h_body += f'void GetParameter(const ObjectInstanceHandle& handler);\n'

        cpp_body += f'\n// @callback({KEY_GET_PARAMETER})\n'
        cpp_body += "void GetParameter(const ObjectInstanceHandle& handler)\n{\n"
        cpp_body += "\tdtig::MParameter paramMessage;\n"

        if self.config.has(KEY_PARAMETERS):
            for p in self.config[KEY_PARAMETERS]:
                cpp_body += f'\tparamMessage.mutable_parameters()->mutable_identifiers()->mutable_names()->add_names("{p[KEY_NAME]}");\n'

        cpp_body += '\tdtig::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_parameter() = paramMessage;\n'
        cpp_body += '\tdtig::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dtig::ReturnCode::SUCCESS)\n\t{\n'
        cpp_body += '\t\tstd::cout << "Failed to get parameters: " << ret.error_message().value() << std::endl;\n'
        cpp_body += '\t\treturn;\n\t}\n\n'

        cpp_body += "\tAttributeHandleValueMap attributes;;\n"
        for index, o in enumerate(self.config[KEY_PARAMETERS]):
            cpp_body += f'\tstd::string id{o[KEY_NAME]} = ret.values().identifiers().names().names({index});\n'
            if o["type"] == "float":
                cpp_body += f'\tdtig::MF32 value{o[KEY_NAME]};\n'
            elif o["type"] == "double":
                cpp_body += f'\tdtig::MF64 value{o[KEY_NAME]};\n'
            elif o["type"] == "int32":
                cpp_body += f'\tdtig::MI32 value{o[KEY_NAME]};\n'
            elif o["type"] == "uint32":
                cpp_body += f'\tdtig::MU32 value{o[KEY_NAME]};\n'

            cpp_body += f'\tif (ret.values().values({index}).UnpackTo(&value{o[KEY_NAME]}))\n'
            cpp_body += "\t{\n"
            cpp_body += f'\t\t{o["type"]} v{o[KEY_NAME]} = value{o[KEY_NAME]}.value();\n'
            cpp_body += f'\t\tattributes[{PARAMETER_HANDLER}s.at(id{o[KEY_NAME]})] = toData<{o["type"]}>(&v{o[KEY_NAME]});\n'
            cpp_body += "\t}\n\n"

        cpp_body += f'\trtiamb->updateAttributeValues(handler, attributes, toVariableLengthData(mName.c_str()));\n'
        cpp_body += "}\n"

        return h_body, cpp_body

    def generate_model_publications(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_PARAMETERS) and not self.config.has(KEY_OUTPUTS):
            return h_body, cpp_body

        h_body += f'\n// @callback({KEY_PUBLISH})\n'
        h_body += f'void SetupPublishers();\n'

        cpp_body += f'\n// @callback({KEY_PUBLISH})\n'
        cpp_body += f'void SetupPublishers()\n'
        cpp_body += "{\n"

        if self.config.has(KEY_PARAMETERS):
            cpp_body += "\tAttributeHandleSet pubAttributes;\n"
            cpp_body += f'\tfor (const auto& pair : {PARAMETER_HANDLER}s)\n'
            cpp_body += "\t\tpubAttributes.insert(pair.second);\n\n"
            cpp_body += f'\trtiamb->publishObjectClassAttributes({PARAMETER_HANDLER}, pubAttributes);\n'

        if self.config.has(KEY_OUTPUTS):
            cpp_body += f'\trtiamb->publishInteractionClass({OUTPUT_HANDLER});\n'

        cpp_body += "}\n"
        return h_body, cpp_body

    def generate_model_subscriptions(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has(KEY_PARAMETERS) and not self.config.has(KEY_OUTPUTS):
            return h_body, cpp_body

        h_body += f'\n// @callback({KEY_SUBSCRIBE})\n'
        h_body += f'void SetupSubscribers();\n'

        cpp_body += f'\n// @callback({KEY_SUBSCRIBE})\n'
        cpp_body += f'void SetupSubscribers()\n'
        cpp_body += "{\n"

        if self.config.has(KEY_PARAMETERS):
            cpp_body += "\tAttributeHandleSet subAttributes;\n"
            cpp_body += f'\tfor (const auto& pair : {PARAMETER_HANDLER}s)\n'
            cpp_body += "\t\tsubAttributes.insert(pair.second);\n\n"
            cpp_body += f'\trtiamb->subscribeObjectClassAttributes({PARAMETER_HANDLER}, subAttributes, true);\n'

        if self.config.has(KEY_INPUTS):
            cpp_body += f'\trtiamb->subscribeInteractionClass({INPUT_HANDLER});\n'

        cpp_body += "}\n"
        return h_body, cpp_body