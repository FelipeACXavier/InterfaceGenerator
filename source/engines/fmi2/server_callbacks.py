# @callback(imports)
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np

# @callback(constructor)
# Engine specific members
self.step       : bool   = False

self.start_time : float  = 0.0
self.stop_time  : float  = 10.0
self.step_size  : float  = 1e-3

self.fmu = None
self.model_name = None
self.value_references = {}


# @callback(initialize)
def parse_initialize(message) -> Message:
    self.model_name = self.parse_and_assign_optional(message, "model_name")
    if self.model_name is None:
        return self.return_code(dtig_code.UNKNOWN_OPTION, f'No model provided')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(advance)
def parse_advance(self, message) -> Message:
    if message.HasField("step_size"):
        step_size = self.parse_number(message.step_size.step)
        if step_size is None:
            return self.return_code(dtig_code.INVALID_OPTION, f'Step must be a float')

        self.step_size = step_size

    self.step = True
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(setinput)
def parse_input(reference, value):
    self.fmu.setReal([self.value_references[reference]], [value])
    return self.return_code(dtig_code.SUCCESS)

# @callback(getoutput)
def parse_output(incoming_references) -> Message:
    n_outputs = len(incoming_references)
    references = [self.value_references[ref] for ref in incoming_references]

    print(f'Getting values: {references} from {incoming_references}')
    values = self.fmu.getReal(references)
    print(f'Values: {values}')

    return values

# @callback(stop)
def parse_stop(message) -> Message:
    print(f'Stopping with: {message.mode}')
    self.step = True
    self.state = State.STOPPED
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(start)
def parse_start(message) -> Message:
    self.start_time = self.parse_and_assign_optional(message, "start_time")
    if self.start_time is None:
        return self.return_code(dtig_code.INVALID_OPTION, f'Start time must be a float')

    self.stop_time = self.parse_and_assign_optional(message, "stop_time")
    if self.stop_time is None:
        return self.return_code(dtig_code.INVALID_OPTION, f'Stop time must be a float')

    if message.HasField("step_size"):
        step_size = self.parse_number(message.step_size.step)
        if step_size is None:
            return self.return_code(dtig_code.INVALID_OPTION, f'Step must be a float')

        self.step_size = step_size

    # For now, we accept either continuous or stepped simulation
    if message.run_mode == dtig_run_mode.CONTINUOUS:
        self.state = State.RUNNING
    elif message.run_mode == dtig_run_mode.STEP:
        self.state = State.STEPPING
    else:
        return self.return_code(dtig_code.INVALID_OPTION, f'Unknown run mode: {message.run_mode}')

    print(f'Starting with: {dtig_run_mode.ERunMode.Name(message.run_mode)}.\nRunning from {self.start_time:0.4f} to {self.stop_time:0.4f} with {self.step_size:0.4f}')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(modelinfo)
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

# @method(public)
def variable_to_info(variable):
    info = dtig_info.MInfo()
    if variable.valueReference:
        info.id.value = variable.valueReference

    if variable.name:
        info.name.value = variable.name

    if variable.type:
        info.type.value = variable.type

    if variable.quantity:
        info.unit.value = variable.quantity

    return info

# @callback(runmodel)
def run_model() -> None:
    with self.condition:
        self.condition.wait_for(lambda: self.state == State.INITIALIZING or self.state == State.STOPPED)
        if self.state == State.STOPPED:
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
        self.condition.wait_for(lambda: self.state == State.STEPPING or self.state == State.RUNNING or self.state == State.STOPPED)

    print(f'Running with state: {self.state.name}')
    # simulation loop
    while time < self.stop_time and self.state != State.STOPPED:
        with self.condition:
            if self.state == State.STEPPING:
                self.condition.wait_for(lambda: self.step)
                print(f'Step: {time:0.4f} out of {self.stop_time:0.4f}')

        # perform one step
        self.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=self.step_size)

        # advance the time
        time += self.step_size

        outputs = self.fmu.getReal(self.value_references.values())[1:]
        rows.append((time, *outputs))

        with self.condition:
            self.step = False
            self.condition.notify_all()

    print(f'FMU simulation done')

    with self.condition:
        if self.state != State.STOPPED:
            self.state = State.IDLE

    if len(rows) > 0:
        # convert the results to a structured NumPy array
        result = np.array(rows, dtype=np.dtype([(k, np.float64) for k in self.value_references.keys()]))
        plot_result(result)


    with self.condition:
        self.condition.wait_for(lambda: self.state == State.STOPPED)

    self.fmu.terminate()
    self.fmu.freeInstance()

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)