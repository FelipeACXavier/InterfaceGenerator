import os

from dtig.common.logging import *
from dtig.common.result import *
from dtig.common.model_configuration_base import ModelConfigurationBase

from dtig.interface.python_generator import ServerGenerator, ClientGenerator

# Callbacks are defined at the module level
engine_folder = os.path.dirname(__file__)

class ServerGeneratorFMI2(ServerGenerator):
  def __init__(self):
    super().__init__()

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    self.config = config
    self.output_file = output_file + "_server.py"

    callback_file = engine_folder + "/server_callbacks.py"

    with open(self.output_file, "w") as file:
      file.write(self.generate_imports())
      file.write(self.generate_states())
      file.write(self.generate_class())
      file.write(self.generate_constructor())
      file.write(self.generate_destructor())
      file.write(self.generate_run())
      file.write(self.generate_run_model())
      generated = self.generate_callbacks(callback_file)
      if not generated.is_success():
        return VoidResult.failed(f'{generated}')
      file.write(generated.value())

      file.write(self.generate_main())

    return VoidResult()

  def generate_imports(self) -> str:
    return super().generate_imports("""
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np
""")

  def generate_constructor(self) -> str:
    contents = super().generate_constructor()
    return contents + """
    # Engine specific members
    self.step       : bool   = False

    self.start_time : float  = 0.0
    self.stop_time  : float  = 10.0
    self.step_size  : float  = 1e-3

    self.fmu = None
    self.model_name = None
    self.value_references = {}
"""

  def generate_run_model(self) -> str:
    return """
  def run_model(self) -> None:
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
            self.step = False
            print(f'Step: {time:0.4f} out of {self.stop_time:0.4f}')

        # perform one step
        self.fmu.doStep(currentCommunicationPoint=time, communicationStepSize=self.step_size)

        # advance the time
        time += self.step_size

        outputs = self.fmu.getReal(self.value_references.values())[1:]
        rows.append((time, *outputs))

    self.fmu.terminate()
    self.fmu.freeInstance()

    if len(rows) > 0:
      # convert the results to a structured NumPy array
      result = np.array(rows, dtype=np.dtype([(k, np.float64) for k in self.value_references.keys()]))
      plot_result(result)

    with self.condition:
      if self.state != State.STOPPED:
        self.state = State.IDLE

      print(f'FMU simulation done')
      self.condition.wait_for(lambda: self.state == State.STOPPED)

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)
"""

# =============================================================
# Client generator

class ClientGeneratorFMI2(ClientGenerator):
  def __init__(self):
    super().__init__()

  def generate(self, output_file : str, config : ModelConfigurationBase) -> VoidResult:
    self.config = config
    self.output_file = output_file + "_client.py"
    callback_file = engine_folder + "/client_callbacks.py"

    with open(self.output_file, "w") as file:
      file.write(self.generate_imports())
      file.write(self.generate_states())
      file.write(self.generate_class())
      file.write(self.generate_constructor())
      file.write(self.generate_destructor())
      file.write(self.generate_run())
      file.write(self.generate_run_model())
      generated = self.generate_callbacks(callback_file)
      if not generated.is_success():
        return VoidResult.failed(f'{generated}')
      file.write(generated.value())

      file.write(self.generate_main())

    return VoidResult()

  def generate_imports(self) -> str:
    return super().generate_imports("""
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result

import shutil
import numpy as np
""")

  def generate_run_model(self) -> str:
    return str()