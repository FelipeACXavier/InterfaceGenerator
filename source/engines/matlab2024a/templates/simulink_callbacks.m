% @callback(initialize)
function returnValue = initialize_callback(message)
  global status;
  global modelName;

  if message.hasModelName()
    modelName = string(message.getModelName().getValue());
    disp(strcat("Using model: ", modelName));
    returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  else
    returnValue = createReturn(dtig.EReturnCode.INVALID_OPTION, "No model provided");
  end
end

% @callback(start)
function returnValue = parse_start(message)
  global status;
  global startTime stopTime stepSize;

  if message.hasStartTime()
    startTime = message.getStartTime().getValue();
  end

  if message.hasStopTime()
    stopTime = message.getStopTime().getValue();
  end

  if message.hasStepSize()
    stepSize = message.getStepSize().getStep();
  end

  % For now, we accept either continuous or stepped simulation
  status.mode = message.getRunMode();
  status.state = dtig.EState.IDLE;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(stop)
function returnValue = parse_stop(~)
  global sm;
  if ~isempty(sm) && sm.Status ~= "inactive"
    pause(sm);
    stop(sm);
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(advance)
function returnValue = parse_advance(message)
  global status sm;
  global stepSize;
  if message.hasStepSize()
    stepSize = message.getStepSize().getStep();
  end

  status.state = dtig.EState.RUNNING;
  step(sm);
  status.state = dtig.EState.WAITING;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(get_status)
function returnValue = parse_get_status()
  global status
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  returnValue.setStatus(dtig.MStatus.newBuilder()...
    .setState(status.state));
end

% @callback(runmodel)
function run_model()
  global h v g e;
  global sm;
  global status modelName;
  global startTime stopTime stepSize;

  % Parameters
  g = 9.81;
  e = 0.7;

  % Inputs and outputs
  h = 1;
  v = 0;

  disp("Waiting for start");
  waitfor(status, "state", dtig.EState.IDLE);

  % Load the model
  sm = simulation(modelName);

  sm = setModelParameter(sm, ...
    StartTime=string(startTime), ...
    StopTime=string(stopTime), ...
    FixedStep=string(stepSize)...
  );

  if status.mode == dtig.ERunMode.STEPPED
    initialize(sm)
    start(sm)
    pause(sm)
    status.state = dtig.EState.WAITING;
  else
    initialize(sm)
    start(sm)
    status.state = dtig.EState.RUNNING;
  end

  % Pause a bit otherwise Simulink fails to start
  pause(1);

  fprintf("Starting with: %s\n", string(status.state));
  fprintf("Running from %.4f to %.4f with step size %.4f\n", startTime, stopTime, stepSize);
end

% @callback(set_input)
function returnValue = set_input(reference, anyValue)
  global modelName;

  handle = getSimulinkBlockHandle(strcat(modelName, "/", reference), true);
  if handle < 0
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
    return;
  end

  value = dtig.Helpers.unpack(anyValue);
  if isempty(value)
    returnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));
    return;
  end

  set_param(handle, "Value", string(value.getValue()));
end

% @callback(get_output)
function returnValue = get_output(references)
  global sm;

  isRunning = (sm.Status == "running");

  if isRunning
    pause(sm);
  end

	dtigOutputs = dtig.MValues.newBuilder();
	nIds = references.size() - 1;
	returnValue = createReturn(dtig.EReturnCode.SUCCESS);

	for i = 0:nIds
		reference = references.get(i);
		dtigOutputs.addIdentifiers(reference);
    value = find(sm.SimulationOutput.logsout, string(reference)).Values.Data(end);

		if reference == "h"
			anyValue = dtig.MF64.newBuilder().setValue(value);
		elseif reference == "v"
			anyValue = dtig.MF64.newBuilder().setValue(value);
		else
			returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown output: ", reference));
			return;
		end

		dtigOutputs.addValues(dtig.Helpers.pack(anyValue));
	end

	returnValue.setValues(dtigOutputs);

  if isRunning
    resume(sm);
  end
end