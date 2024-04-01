import os
import re

from pathlib import Path

from dtig.common.keys import *
from dtig.common.result import *
from dtig.common.logging import *
from dtig.common.model_configuration_base import ModelConfigurationBase

from dtig.interface.cpp_generator import HppGenerator, CppGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__) + "/templates"

PARAMETER_HANDLER = "mAttributeHandler"
INPUT_HANDLER = "mInputHandler"
OUTPUT_HANDLER = "mOutputHandler"

class ClientGeneratorRTI1516():
    def __init__(self, output_file):
        self.federate_h_callbacks = f'{Path(output_file).parent.absolute()}/federate_callbacks.h'
        self.federate_cpp_callbacks = f'{Path(output_file).parent.absolute()}/federate_callbacks.cpp'

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
        federate_cpp.callbacks[KEY_CALLBACK][KEY_INITIALIZE] = {KEY_NAME : "",  KEY_BODY : "", KEY_SELF: False}

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
        federate_hpp.new_callback("ambassador_header", {KEY_NAME: Path(ambassador_header).name, KEY_BODY: "", KEY_SELF: False})
        federate_cpp.new_callback("ambassador", ambassador_name)
        federate_cpp.new_callback("ambassador_header", {KEY_NAME: Path(ambassador_header).name, KEY_BODY: "", KEY_SELF: False})

        generated = federate_hpp.generate(config)
        if not generated:
            return generated

        generated = federate_cpp.generate(config)
        if not generated:
            return generated

        return VoidResult()

    def set_client_info(self, server_cmd, server_path):
        self.server_cmd  = {KEY_NAME: server_cmd,  KEY_BODY: "", KEY_SELF: False}
        self.server_path = {KEY_NAME: server_path, KEY_BODY: "", KEY_SELF: False}

    def generate_model_config(self):
        h_body = f'@callback({KEY_MEMBER})\n'
        cpp_body = f'@callback({KEY_INITIALIZE})\n'

        h, cpp = self.generate_model_parameters()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_inputs()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_outputs()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_set_input()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_get_output()
        h_body += h
        cpp_body += cpp

        h, cpp = self.generate_model_subscriptions()
        h_body += h
        cpp_body += cpp

        with open(self.federate_h_callbacks, "w") as f:
            f.write(h_body)

        with open(self.federate_cpp_callbacks, "w") as f:
            f.write(cpp_body)

    def generate_model_inputs(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has("inputs"):
            namespaces = dict()
            for p in self.config["inputs"]:
                if p["namespace"] not in namespaces.keys():
                    namespaces[p["namespace"]] = [p]
                else:
                    namespaces[p["namespace"]].append(p)

            if len(namespaces.keys()) != 1:
                LOG_ERROR(f'Currently, the tool only supports inputs in a single namespace')
                return ""

            h_body += f'std::map<rti1516::ParameterHandle, std::string> {INPUT_HANDLER}s;\n'
            for k, parameters in namespaces.items():
                h_body += f'rti1516::InteractionClassHandle {INPUT_HANDLER};\n'
                cpp_body += f'\t\t{INPUT_HANDLER} = rtiamb->getInteractionClassHandle(L"{k}");\n'

                for p in parameters:
                    cpp_body += f'\t\t{INPUT_HANDLER}s.insert({{rtiamb->getParameterHandle({INPUT_HANDLER}, L"{p["name"]}"), "{p["name"]}"}});\n'

        return h_body, cpp_body

    def generate_model_outputs(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has("outputs"):
            namespaces = dict()
            for p in self.config["outputs"]:
                if p["namespace"] not in namespaces.keys():
                    namespaces[p["namespace"]] = [p]
                else:
                    namespaces[p["namespace"]].append(p)

            if len(namespaces.keys()) != 1:
                LOG_ERROR(f'Currently, the tool only supports outputs in a single namespace')
                return ""

            h_body += f'std::map<std::string, rti1516::ParameterHandle> {OUTPUT_HANDLER}s;\n'
            for k, parameters in namespaces.items():
                h_body += f'rti1516::InteractionClassHandle {OUTPUT_HANDLER};\n'
                cpp_body += f'\t\t{OUTPUT_HANDLER} = rtiamb->getInteractionClassHandle(L"{k}");\n'

                for p in parameters:
                    cpp_body += f'\t\t{OUTPUT_HANDLER}s.insert({{"{p["name"]}", rtiamb->getParameterHandle({OUTPUT_HANDLER}, L"{p["name"]}")}});\n'

        return h_body, cpp_body

    def generate_model_parameters(self) -> str:
        h_body = ""
        cpp_body = ""

        if self.config.has("parameters"):
            namespaces = dict()
            for p in self.config["parameters"]:
                if p["namespace"] not in namespaces.keys():
                    namespaces[p["namespace"]] = [p]
                else:
                    namespaces[p["namespace"]].append(p)

            if len(namespaces.keys()) != 1:
                LOG_ERROR(f'Currently, the tool only supports parameters in a single namespace')
                return ""

            h_body += f'rti1516::AttributeHandleSet {PARAMETER_HANDLER}s;\n'
            for k, parameters in namespaces.items():
                h_body += f'rti1516::ObjectClassHandle {PARAMETER_HANDLER};\n'
                cpp_body += f'\t\t{PARAMETER_HANDLER} = rtiamb->getObjectClassHandle(L"{k}");\n'

                for p in parameters:
                    cpp_body += f'\t\t{PARAMETER_HANDLER}s.insert(rtiamb->getAttributeHandle({PARAMETER_HANDLER}, L"{p["name"]}"));\n'

        return h_body, cpp_body

    def generate_model_set_input(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has("inputs"):
            return h_body, cpp_body

        h_body = f'\n@callback({KEY_SET_INPUT})\n'
        h_body += "void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues);\n"

        cpp_body = f'\n@callback({KEY_SET_INPUT})\n'
        cpp_body += "void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues)\n{\n"
        cpp_body += "\tdti::MInput inputMessage;\n"

        # for o in self.config["inputs"]:
        cpp_body += "\tfor (auto i = parameterValues.begin(); i != parameterValues.end(); ++i)\n"
        cpp_body += "\t{\n"
        cpp_body += "\t\tstd::string item = mInputHandlers[i->first];\n"
        cpp_body += "\t\tinputMessage.mutable_inputs()->mutable_identifiers()->mutable_names()->add_names(item);\n"
        for i, cfg in enumerate(self.config["inputs"]):
            cpp_body += f'\t\t{"if" if i == 0 else "else if"} (item == "{cfg["name"]}")\n'
            cpp_body += "\t\t{\n"
            if cfg["type"] == "float":
                cpp_body += f'\t\t\tdti::MF32 value;\n'
            elif cfg["type"] == "double":
                cpp_body += f'\t\t\tdti::MF64 value;\n'
            elif cfg["type"] == "int32":
                cpp_body += f'\t\t\tdti::MI32 value;\n'
            elif cfg["type"] == "uint32":
                cpp_body += f'\t\t\tdti::MU32 value;\n'

            cpp_body += f'\t\t\tvalue.set_value(fromData<{cfg["type"]}>(i->second));\n'
            cpp_body += "\t\t\tinputMessage.mutable_inputs()->add_values()->PackFrom(value);\n"

            cpp_body += "\t\t}\n"

        cpp_body += "\t\telse\n"
        cpp_body += "\t\t{\n"
        cpp_body += '\t\t\tLOG_ERROR("Unknown input: %s", item.c_str());\n'
        cpp_body += '\t\t\treturn;\n'
        cpp_body += "\t\t}\n"

        cpp_body += "\t}\n\n"

        cpp_body += '\tdti::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_input() = inputMessage;\n'
        cpp_body += '\tdti::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dti::ReturnCode::SUCCESS)\n\t'
        cpp_body += '\tLOG_ERROR("Failed to set inputs: %s", ret.error_message().value().c_str());\n'

        cpp_body += '}\n'

        return h_body, cpp_body

    def generate_model_get_output(self) -> str:
        h_body = ""
        cpp_body = ""
        if not self.config.has("outputs"):
            return h_body, cpp_body

        h_body += f'\n@callback({KEY_GET_OUTPUT})\n'
        h_body += f'void GetOutput();\n'

        cpp_body += f'\n@callback({KEY_GET_OUTPUT})\n'
        cpp_body += "void GetOutput()\n{\n"
        cpp_body += "\tdti::MOutput outputMessage;\n"

        if self.config.has("outputs"):
            for o in self.config["outputs"]:
                cpp_body += f'\toutputMessage.mutable_outputs()->mutable_identifiers()->mutable_names()->add_names("{o["name"]}");\n'

        cpp_body += '\tdti::MDTMessage message;\n'
        cpp_body += '\t*message.mutable_output() = outputMessage;\n'
        cpp_body += '\tdti::MReturnValue ret = SendMessage(message);\n'
        cpp_body += '\tif (ret.code() != dti::ReturnCode::SUCCESS)\n\t{\n'
        cpp_body += '\t\tLOG_ERROR("Failed to get outputs: %s", ret.error_message().value().c_str());\n'
        cpp_body += '\t\treturn;\n\t}\n\n'

        cpp_body += "\tParameterHandleValueMap parameters;\n"
        # cpp_body += "for (int i = 0; i < ret.values().values_size(); ++i)\n{{"
        for index, o in enumerate(self.config["outputs"]):
            cpp_body += f'\tstd::string id{o["name"]} = ret.values().identifiers().names().names({index});\n'
            if o["type"] == "float":
                cpp_body += f'\tdti::MF32 value{o["name"]};\n'
            elif o["type"] == "double":
                cpp_body += f'\tdti::MF64 value{o["name"]};\n'
            elif o["type"] == "int32":
                cpp_body += f'\tdti::MI32 value{o["name"]};\n'
            elif o["type"] == "uint32":
                cpp_body += f'\tdti::MU32 value{o["name"]};\n'

            cpp_body += f'\tif (ret.values().values({index}).UnpackTo(&value{o["name"]}))\n'
            cpp_body += "\t{\n"
            cpp_body += f'\t\t{o["type"]} v{o["name"]} = value{o["name"]}.value();\n'
            cpp_body += f'\t\tparameters[mOutputHandlers.at(id{o["name"]})] = toData<{o["type"]}>(&v{o["name"]});\n'
            cpp_body += "\t}\n\n"

        cpp_body += f'\trtiamb->sendInteraction({OUTPUT_HANDLER}, parameters, toVariableLengthData(mName.c_str()));\n'
        cpp_body += "}\n"

        return h_body, cpp_body

    def generate_model_subscriptions(self) -> str:
        h_body = ""
        cpp_body = f'\n@callback({KEY_SUBSCRIBE})\n'

        if self.config.has("parameters"):
            cpp_body += f'\trtiamb->publishObjectClassAttributes({PARAMETER_HANDLER}, {PARAMETER_HANDLER}s);\n'
            cpp_body += f'\trtiamb->subscribeObjectClassAttributes({PARAMETER_HANDLER}, {PARAMETER_HANDLER}s, true);\n'

        if self.config.has("inputs"):
            cpp_body += f'\trtiamb->subscribeInteractionClass({INPUT_HANDLER});\n'

        if self.config.has("outputs"):
            cpp_body += f'\trtiamb->publishInteractionClass({OUTPUT_HANDLER});\n'

        return h_body, cpp_body