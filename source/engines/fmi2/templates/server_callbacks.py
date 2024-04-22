<DTIG_CALLBACK(IMPORTS)>
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np

<DTIG_CLASSNAME>
FMI2Wrapper

<DTIG_CALLBACK(CONSTRUCTOR)>
# Engine specific members
self.start_time : float  = 0.0
self.stop_time  : float  = 10.0
self.step_size  : float  = 1e-3

self.fmu = None
self.model_name = None
self.value_references = {}

<DTIG_CALLBACK(INITIALIZE)>
def parse_initialize(message) -> Message:
    if message.HasField("model_name"):
        self.model_name = message.model_name.value
    else:
        return self.return_code(dtig_code.INVALID_OPTION, f'No model provided')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(START)>
def parse_start(message) -> Message:
    if message.HasField("start_time"):
        self.start_time = message.start_time.value

    if message.HasField("stop_time"):
        self.stop_time = message.stop_time.value

    if message.HasField("step_size"):
        # TODO: Add support for micro steps
        self.step_size = message.step_size.step

    # For now, we accept either continuous or stepped simulation
    if message.run_mode == dtig_run_mode.UNKNOWN:
        return self.return_code(dtig_code.INVALID_OPTION, f'Unknown run mode: {message.run_mode}')

    self.mode = message.run_mode
    self.state = dtig_state.WAITING if self.mode == dtig_run_mode.STEPPED else dtig_state.RUNNING

    print(f'Starting with: {dtig_run_mode.ERunMode.Name(self.mode)}.')
    print(f'Running from {self.start_time:0.4f} to {self.stop_time:0.4f} with {self.step_size:0.4f}')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(STOP)>
def parse_stop(message) -> Message:
    print(f'Stopping with: {message.mode}')
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(ADVANCE)>
def parse_advance(self, message) -> Message:
    if message.HasField("step_size"):
        self.step_size = message.step_size.step

    self.state = dtig_state.RUNNING
    return self.return_code(dtig_code.SUCCESS)

<DTIG_CALLBACK(GET_STATUS)>
def parse_model_info() -> Message:
    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    return_value.status.state = self.state
    return return_value

<DTIG_METHOD(PUBLIC)>
def variable_to_info(variable):
    info = dtig_info.MInfo()
    if variable.valueReference:
        info.id.value = variable.valueReference

    if variable:
        info.value = variable

    if variable.type:
        info.type.value = variable.type

    if variable.quantity:
        info.unit.value = variable.quantity

    return info

<DTIG_CALLBACK(RUNMODEL)>
def run_model() -> None:
    while True:
        with self.condition:
            self.condition.wait_for(lambda: self.state == dtig_state.INITIALIZED or self.state == dtig_state.STOPPED)
            if self.state == dtig_state.STOPPED:
                return

        print(f'Initializing FMU: {self.model_name}')

        # read the model description
        try:
            model_description = read_model_description(self.model_name)
            break
        except Exception as e:
            print(f'Failed to open model: {self.model_name}')
            with self.condition:
                self.state = dtig_state.UNINITIALIZED

    # collect the value references
    for variable in model_description.modelVariables:
        print(f'{variable.name} with type {variable.type}')
        self.value_references[variable.name] = variable.valueReference

    # extract the FMU
    unzipdir = extract(self.model_name)

    self.fmu = FMU2Slave(guid=model_description.guid,
                         unzipDirectory=unzipdir,
                         modelIdentifier=model_description.coSimulation.modelIdentifier,
                         instanceName='instance1')

    # initialize
    self.fmu.instantiate()
    self.fmu.setupExperiment(startTime=self.start_time)
    self.fmu.enterInitializationMode()
    self.fmu.exitInitializationMode()

    while self.state != dtig_state.STOPPED:
        with self.condition:
            self.condition.wait_for(lambda: self.state == dtig_state.RUNNING or self.state == dtig_state.STOPPED)

        rows : list = []  # list to record the results
        time : float = self.start_time

        print(f'Running with state: {self.state} and {time} vs {self.start_time}')
        # simulation loop
        while time < self.stop_time and self.state != dtig_state.STOPPED:
            with self.condition:
                if self.mode == dtig_run_mode.STEPPED:
                    self.condition.wait_for(lambda: self.state == dtig_state.RUNNING or self.state == dtig_state.STOPPED)
                    print(f'Step: {time:0.4f} out of {self.stop_time:0.4f}')

            # perform one step
            self.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=self.step_size)

            # advance the time
            time += self.step_size

            outputs = self.fmu.getReal(self.value_references.values())[1:]
            rows.append((time, *outputs))

            with self.condition:
                if self.mode == dtig_run_mode.STEPPED and self.state != dtig_state.STOPPED:
                    self.state = dtig_state.WAITING

        print(f'FMU simulation done')

        with self.condition:
            if self.state != dtig_state.STOPPED:
                self.state = dtig_state.IDLE

        if len(rows) > 0:
            # convert the results to a structured NumPy array
            result = np.array(rows, dtype=np.dtype([(k, np.float64) for k in self.value_references.keys()]))
            plot_result(result)

    self.fmu.terminate()
    self.fmu.freeInstance()

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)

<DTIG_CALLBACK(SET_INPUT)>
def set_inputs(reference, any_value):
    DTIG_IF(NOT DTIG_INPUTS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no inputs")
    DTIG_ELSE

    DTIG_FOR(DTIG_INPUTS)

    DTIG_IF(DTIG_INDEX == 0)
    if reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_ELSE
    elif reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_END_IF
        value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
        if not any_value.Unpack(value):
            return self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {reference}")
        self.fmu.setDTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)([self.value_references[reference]], [value.value])
        return self.return_code(dtig_code.SUCCESS)

    DTIG_END_FOR
    else:
        return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown input: {reference}")
    DTIG_END_IF

<DTIG_CALLBACK(GET_OUTPUT)>
def get_outputs(references):
    DTIG_IF(NOT DTIG_OUTPUTS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no outputs")
    DTIG_ELSE
    return_message = self.return_code(dtig_code.SUCCESS)
    for reference in references:
        DTIG_FOR(DTIG_OUTPUTS)
        DTIG_IF(DTIG_INDEX == 0)
        if reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF
            any_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
            any_value.value = self.fmu.getDTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)([self.value_references[reference]])[0]
        DTIG_END_FOR
        else:
            return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")

        any_msg = any_pb2.Any()
        any_msg.Pack(any_value)
        return_message.values.identifiers.append(reference)
        return_message.values.values.append(any_msg)

    return return_message
    DTIG_END_IF

<DTIG_CALLBACK(SET_PARAMETER)>
def set_parameters(reference, any_value):
    DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no parameters")
    DTIG_ELSE

    DTIG_FOR(DTIG_PARAMETERS)

    DTIG_IF(DTIG_INDEX == 0)
    if reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_ELSE
    elif reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_END_IF
        value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
        if not any_value.Unpack(value):
            return self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {reference}")
        self.fmu.setDTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)([self.value_references[reference]], [value.value])
        return self.return_code(dtig_code.SUCCESS)

    DTIG_END_FOR
    else:
        return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown input: {reference}")
    DTIG_END_IF

<DTIG_CALLBACK(GET_PARAMETER)>
def get_parameter(references):
    DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no parameters")
    DTIG_ELSE
    return_message = self.return_code(dtig_code.SUCCESS)
    for reference in references:
        DTIG_FOR(DTIG_PARAMETERS)
        DTIG_IF(DTIG_INDEX == 0)
        if reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF
            any_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
            any_value.value = self.fmu.getDTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)([self.value_references[reference]])[0]
        DTIG_END_FOR
        else:
            return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")

        any_msg = any_pb2.Any()
        any_msg.Pack(any_value)
        return_message.values.identifiers.append(reference)
        return_message.values.values.append(any_msg)

    return return_message
    DTIG_END_IF