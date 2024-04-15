# @callback(imports)
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np

# @classname
FMI2Wrapper

# @callback(constructor)
# Engine specific members
self.start_time : float  = 0.0
self.stop_time  : float  = 10.0
self.step_size  : float  = 1e-3

self.fmu = None
self.model_name = None
self.value_references = {}

# @callback(initialize)
def parse_initialize(message) -> Message:
    if message.HasField("model_name"):
        self.model_name = message.model_name.value
    else:
        return self.return_code(dtig_code.INVALID_OPTION, f'No model provided')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(start)
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

# @callback(stop)
def parse_stop(message) -> Message:
    print(f'Stopping with: {message.mode}')
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(advance)
def parse_advance(self, message) -> Message:
    if message.HasField("step_size"):
        self.step_size = message.step_size.step

    self.state = dtig_state.RUNNING
    return self.return_code(dtig_code.SUCCESS)

# @callback(model_info)
def parse_model_info() -> Message:
    if not self.model_name:
        return self.return_code(dtig_code.FAILURE, f'Model is not yet known')

    model_description = read_model_description(self.model_name)

    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    for variable in model_description.modelVariables:
        if variable.causality == "input":
            return_value.model_info.inputs.append(self.variable_to_info(variable))
        elif variable.causality == "output":
            return_value.model_info.outputs.append(self.variable_to_info(variable))
        elif variable.causality == "parameter":
            return_value.model_info.parameters.append(self.variable_to_info(variable))

    return return_value

# @callback(get_status)
def parse_model_info() -> Message:
    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    return_value.status.state = self.state
    return return_value

# @method(public)
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

# @callback(runmodel)
def run_model() -> None:
    with self.condition:
        self.condition.wait_for(lambda: self.state == dtig_state.INITIALIZED or self.state == dtig_state.STOPPED)
        if self.state == dtig_state.STOPPED:
            return

    print(f'Initializing FMU: {self.model_name}')

    # read the model description
    model_description = read_model_description(self.model_name)

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

    rows : list = []  # list to record the results
    time : float = self.start_time

    with self.condition:
        self.condition.wait_for(lambda: self.mode != dtig_run_mode.UNKNOWN or self.state == dtig_state.STOPPED)

    print(f'Running with state: {self.state}')
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


    with self.condition:
        self.condition.wait_for(lambda: self.state == dtig_state.STOPPED)

    self.fmu.terminate()
    self.fmu.freeInstance()

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)
