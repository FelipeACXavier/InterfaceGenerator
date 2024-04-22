<DTIG_CALLBACK(CONSTRUCTOR)>
self.previous_message = None

<DTIG_CALLBACK(RUNCLIENT)>
def run_client(self, sock):
    previous_option = "0"
    while self.running:
        option = self.print_menu()
        if option == "0":
            DTIG>PARSE(STOP)(sock)
        elif option == "1":
            DTIG>PARSE(INITIALIZE)(sock)
        elif option == "2":
            DTIG>PARSE(START)(sock)
        elif option == "3":
            DTIG>PARSE(ADVANCE)(sock)
        elif option == "4":
            DTIG>PARSE(SET_INPUT)(sock)
        elif option == "5":
            DTIG>PARSE(GET_OUTPUT)(sock)
        elif option == "6":
            DTIG>PARSE(SET_PARAMETER)(sock)
        elif option == "7":
            DTIG>PARSE(GET_PARAMETER)(sock)
        elif option == "8":
            DTIG>PARSE(MODEL_INFO)(sock)
        elif option == "9":
            DTIG>PARSE(GET_STATUS)(sock)
        elif self.previous_message:
            LOG_INFO(f'Using previous command')
            self.send_message(sock, self.previous_message)
        else:
            LOG_ERROR(f'Unknown command: {option}')

<DTIG_CALLBACK(STOP)>
def stop(self, sock):
    message = dtig_message.MDTMessage()
    message.stop.mode = dtig_stop_mode.CLEAN
    self.send_message(sock, message)

<DTIG_CALLBACK(INITIALIZE)>
def initialize(self, sock):
    message = dtig_message.MDTMessage()
    model_name = input(f"What is the model name? (Current: {self.model_name})").strip()
    if model_name:
        self.model_name = model_name
    elif not self.model_name:
        LOG_ERROR("No model name provided")

    message.initialize.model_name.value = self.model_name
    self.send_message(sock, message)

<DTIG_CALLBACK(START)>
def start(self, sock):
    message = dtig_message.MDTMessage()
    message.start.start_time.value = float(input("What start time? "))
    message.start.stop_time.value  = float(input("What stop time? "))
    message.start.step_size.step   = float(input("What step size? "))
    print("Available modes:")
    print(" 1 - Stepped")
    print(" 2 - Continuous")
    while True:
        mode = int(input("What mode? ").strip())
        if mode == 1:
            message.start.run_mode = dtig_run_mode.STEPPED
            break
        elif mode == 2:
            message.start.run_mode = dtig_run_mode.CONTINUOUS
            break
        else:
            LOG_WARNING(f'Unknown mode: {mode}')

    self.send_message(sock, message)

<DTIG_CALLBACK(ADVANCE)>
def advance(self, sock):
    message = dtig_message.MDTMessage()
    message.advance.step_size.step = float(input("What step size? "))
    self.send_message(sock, message)

<DTIG_CALLBACK(SET_INPUT)>
def set_input(self, sock):
    message = dtig_message.MDTMessage()
    DTIG_IF(DTIG_PARAMETERS_LENGTH)
    print("Available inputs:")
    DTIG_FOR(DTIG_INPUTS)
    print(f'  DTIG_ITEM_NAME - DTIG_ITEM_TYPE')
    DTIG_END_FOR
    DTIG_END_IF

    input_name = "default"
    while input_name:
        input_name = input("Which input? ")
        if not len(input_name):
            break

        DTIG_FOR(DTIG_INPUTS)
        DTIG_IF(DTIG_INDEX == 0)

        if input_name == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif input_name == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF
            typed_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
            DTIG_IF(DTIG_ITEM_TYPE == TYPE_FORCE)
            input_value = float(input("Force value? ").strip())
            typed_value.value.value = input_value

            input_object = input("Force on which object? (e.g. Box)").strip()
            typed_value.object.value = input_object

            input_reference = input("Force on which reference? (e.g. Face2)").strip()
            typed_value.reference.value = i_reference

            input_direction input("Force on which direction? (e.g. -Z)").strip()
            typed_value.direction.value = i_direction

            DTIG_ELSE
            input_value = DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)(input("Input value? ").strip())
            typed_value.value = input_value
            DTIG_END_IF


        DTIG_END_FOR
        else:
            LOG_WARNING(f'Unknown parameter: {input_name}')
            continue

        any_msg = any_pb2.Any()
        any_msg.Pack(typed_value)
        message.set_input.inputs.identifiers.append(input_name)
        message.set_input.inputs.values.append(any_msg)

    self.send_message(sock, message)

    def handler(response):
        if response.HasField("values"):
            for any_value in response.values.values:
                DTIG_FOR(DTIG_PARAMETERS)
                DTIG_IF(DTIG_INDEX == 0)
                if param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_ELSE
                elif param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_END_IF
                    value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
                    if any_value.Unpack(value):
                        LOG_INFO(f'DTIG_ITEM_NAME: {value.value}')
                DTIG_END_FOR

    self.send_message(sock, message, handler)

<DTIG_CALLBACK(GET_OUTPUT)>
def get_output(self, sock):
    message = dtig_message.MDTMessage()
    DTIG_FOR(DTIG_OUTPUTS)
        message.get_output.outputs.identifiers.append(DTIG_STR(DTIG_ITEM_NAME))
    DTIG_END_FOR

    def handler(response):
        if response.HasField("values"):
            for i in range(len(response.values.values)):
                param = response.values.identifiers[i]
                any_value = response.values.values[i]
                DTIG_FOR(DTIG_OUTPUTS)
                DTIG_IF(DTIG_INDEX == 0)
                if param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_ELSE
                elif param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_END_IF
                    value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
                    if any_value.Unpack(value):
                        LOG_INFO(f'DTIG_ITEM_NAME: {value.value}')
                DTIG_END_FOR

    self.send_message(sock, message, handler)

<DTIG_CALLBACK(SET_PARAMETER)>
def set_parameter(self, sock):
    message = dtig_message.MDTMessage()
    DTIG_IF(DTIG_PARAMETERS_LENGTH)
    print("Available parameters:")
    DTIG_FOR(DTIG_PARAMETERS)
    print(f'  DTIG_ITEM_NAME - DTIG_ITEM_TYPE')
    DTIG_END_FOR
    DTIG_END_IF

    param_name = "default"
    while param_name:
        param_name = input("Which parameter? ")
        if not len(param_name):
            break

        DTIG_FOR(DTIG_PARAMETERS)
        DTIG_IF(DTIG_INDEX == 0)

        if param_name == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif param_name == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF
            typed_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
            DTIG_IF(DTIG_ITEM_TYPE == TYPE_FORCE)
            param_value = float(input("Force value? ").strip())
            typed_value.value.value = param_value

            param_object = input("Force on which object? (e.g. Box)").strip()
            typed_value.object.value = param_object

            param_reference = input("Force on which reference? (e.g. Face2)").strip()
            typed_value.reference.value = i_reference

            param_direction input("Force on which direction? (e.g. -Z)").strip()
            typed_value.direction.value = i_direction

            DTIG_ELSE
            param_value = DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)(input("Input value? ").strip())
            typed_value.value = param_value
            DTIG_END_IF


        DTIG_END_FOR
        else:
            LOG_WARNING(f'Unknown parameter: {param_name}')
            continue

        any_msg = any_pb2.Any()
        any_msg.Pack(typed_value)
        message.set_parameter.parameters.identifiers.append(param_name)
        message.set_parameter.parameters.values.append(any_msg)

    self.send_message(sock, message)

    def handler(response):
        if response.HasField("values"):
            for any_value in response.values.values:
                DTIG_FOR(DTIG_PARAMETERS)
                DTIG_IF(DTIG_INDEX == 0)
                if param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_ELSE
                elif param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_END_IF
                    value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
                    if any_value.Unpack(value):
                        LOG_INFO(f'DTIG_ITEM_NAME: {value.value}')
                DTIG_END_FOR

    self.send_message(sock, message, handler)

<DTIG_CALLBACK(GET_PARAMETER)>
def get_parameter(self, sock):
    message = dtig_message.MDTMessage()
    DTIG_FOR(DTIG_PARAMETERS)
        message.get_parameter.parameters.identifiers.append(DTIG_STR(DTIG_ITEM_NAME))
    DTIG_END_FOR

    def handler(response):
        if response.HasField("values"):
            for i in range(len(response.values.values)):
                param = response.values.identifiers[i]
                any_value = response.values.values[i]
                DTIG_FOR(DTIG_PARAMETERS)
                DTIG_IF(DTIG_INDEX == 0)
                if param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_ELSE
                elif param == DTIG_STR(DTIG_ITEM_NAME):
                DTIG_END_IF
                    value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
                    if any_value.Unpack(value):
                        LOG_INFO(f'DTIG_ITEM_NAME: {value.value}')
                DTIG_END_FOR

    self.send_message(sock, message, handler)

<DTIG_CALLBACK(MODEL_INFO)>
def model_info(self, sock):
    message = dtig_message.MDTMessage()
    message.model_info.request = True

    def handler(response):
        if response.HasField("model_info"):
            if len(response.model_info.inputs):
                print(f'Input:')
                for info in response.model_info.inputs:
                    self.print_info(info)

            if len(response.model_info.outputs):
                print(f'Output:')
                for info in response.model_info.outputs:
                    self.print_info(info)

            if len(response.model_info.parameters):
                print(f'Parameter:')
                for info in response.model_info.parameters:
                    self.print_info(info)

    self.send_message(sock, message, handler)

<DTIG_CALLBACK(GET_STATUS)>
def status(self, sock):
    message = dtig_message.MDTMessage()
    message.get_status.request = True

    def handler(response):
        if response.HasField("status"):
            LOG_INFO(f"Current status: {dtig_state.EState.Name(response.status.state)}")

    response = self.send_message(sock, message, handler)

<DTIG_METHOD(PUBLIC)>
def send_message(self, sock, message, handler=None):
    data_to_send = message.SerializeToString()
    sock.sendall(data_to_send)

    received_data = sock.recv(1024)
    if not received_data:
        print("Server stopped")
        self.running = False
        return

    self.previous_message = message

    response = dtig_return.MReturnValue()
    response.ParseFromString(received_data)

    if response.code == dtig_code.SUCCESS:
        if handler:
            handler(response)
        return

    LOG_ERROR(f'Failed with code: {response.code}')
    if response.HasField("error_message"):
        LOG_ERROR(f'Message: {response.error_message.value}')

<DTIG_METHOD(PUBLIC)>
def print_menu(self):
    print("Options:")
    print("  0 - Stop model")
    print("  1 - Initialize model")
    print("  2 - Run model")
    print("  3 - Advance model in stepped mode")
    print("  4 - Set input")
    print("  5 - Get output")
    print("  6 - Set parameter")
    print("  7 - Get Parameter")
    print("  8 - Model info")
    print("  9 - Model status")
    return input("What should we do? ").strip()

<DTIG_METHOD(PUBLIC)>
def print_info(self, info):
    if info.HasField("name"):
        print(f'  Name: {info.name.value}')
    if info.HasField("id"):
        print(f'    Id: {info.id.value}')
    if info.HasField("description"):
        print(f'    Description: {info.description.value}')
    if info.HasField("type"):
        print(f'    Type: {info.type.value}')
    if info.HasField("unit"):
        print(f'    Unit: {info.unit.value}')
    if info.HasField("namespace"):
        print(f'    Namespace: {info.namespace.value}')
    if info.HasField("modifier"):
        print(f'    Modifier: {info.modifier.value}')
    if info.HasField("default"):
        print(f'    Default: {info.default.value}')
