@callback(initialize)
def parse_initialize(message : dti_initialize.MInitialize) -> Message:
  self.model_name = self.parse_and_assign_optional(message, "model_name")
  if self.model_name is None:
    return self.return_code(dti_code.UNKNOWN_OPTION, f'No model provided')

  return dti_return.MReturnValue(code=dti_code.SUCCESS)

@callback(advance)
def parse_advance(self, message : dti_advance.MAdvance) -> Message:
  if message.HasField("step_size"):
    step_size = self.parse_number(message.step_size.step)
    if step_size is None:
      return self.return_code(dti_code.INVALID_OPTION, f'Step must be a float')

    self.step_size = step_size

  self.step = True
  return dti_return.MReturnValue(code=dti_code.SUCCESS)

@callback(set_input)
def parse_input(reference, value):
  self.fmu.setReal([self.value_references[reference]], [value])
  return self.return_code(dti_code.SUCCESS)

@callback(get_output)
def parse_output(incoming_references) -> Message:
  n_outputs = len(incoming_references)
  references = [self.value_references[ref] for ref in incoming_references]

  print(f'Getting values: {references}')
  values = self.fmu.getReal(references)
  print(f'Values: {values}')

  return values

@callback(stop)
def parse_stop(self, message : dti_stop.MStop) -> Message:
  print(f'Stopping with: {message.mode}')
  self.step = True
  self.state = State.STOPPED
  return dti_return.MReturnValue(code=dti_code.SUCCESS)

@callback(start)
def parse_start(self, message : dti_start.MStart) -> Message:
  self.start_time = self.parse_and_assign_optional(message, "start_time")
  if self.start_time is None:
    return self.return_code(dti_code.INVALID_OPTION, f'Start time must be a float')

  self.stop_time = self.parse_and_assign_optional(message, "stop_time")
  if self.stop_time is None:
    return self.return_code(dti_code.INVALID_OPTION, f'Stop time must be a float')

  if message.HasField("step_size"):
    step_size = self.parse_number(message.step_size.step)
    if step_size is None:
      return self.return_code(dti_code.INVALID_OPTION, f'Step must be a float')

    self.step_size = step_size

  # For now, we accept either continuous or stepped simulation
  if message.run_mode == dti_run_mode.CONTINUOUS:
    self.state = State.RUNNING
  elif message.run_mode == dti_run_mode.STEP:
    self.state = State.STEPPING
  else:
    return self.return_code(dti_code.INVALID_OPTION, f'Unknown run mode: {message.run_mode}')

  self.step = True
  print(f'Starting with: {dti_run_mode.ERunMode.Name(message.run_mode)}.\nRunning from {self.start_time:0.4f} to {self.stop_time:0.4f} with {self.step_size:0.4f}')

  return dti_return.MReturnValue(code=dti_code.SUCCESS)
