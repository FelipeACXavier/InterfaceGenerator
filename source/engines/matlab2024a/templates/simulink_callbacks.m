<DTIG_CALLBACK(INITIALIZE)>
function returnValue = initialize_callback(message)
  global status;
  global sm;
  global modelName;

  if message.hasModelName()
    modelName = string(message.getModelName().getValue());
    disp(strcat("Using model: ", modelName));
    returnValue = createReturn(dtig.EReturnCode.SUCCESS);

    sm = simulation(modelName);
  else
    returnValue = createReturn(dtig.EReturnCode.INVALID_OPTION, "No model provided");
  end
end

<DTIG_CALLBACK(START)>
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
  if status.mode == dtig.ERunMode.STEPPED
    status.state = dtig.EState.WAITING;
  else
    status.state = dtig.EState.RUNNING;
  end
  status.wait = false;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

<DTIG_CALLBACK(STOP)>
function returnValue = parse_stop(~)
  global sm;
  if ~isempty(sm) && sm.Status ~= "inactive"
    pause(sm);
  end

  stop(sm);
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

<DTIG_CALLBACK(ADVANCE)>
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

<DTIG_CALLBACK(GET_STATUS)>
function returnValue = parse_get_status()
  global status
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  returnValue.setStatus(dtig.MStatus.newBuilder()...
    .setState(status.state));
end

<DTIG_CALLBACK(RUNMODEL)>
function run_model()
  global sm;
  global status modelName;
  global startTime stopTime stepSize;

  % Initial values
  DTIG_FOR(DTIG_PARAMETERS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  DTIG_FOR(DTIG_INPUTS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  DTIG_FOR(DTIG_OUTPUTS)
  DTIG_IF(DTIG_ITEM_NAME NOT IN DTIG_INPUTS_NAMES)
  global DTIG_ITEM_NAME;
  DTIG_END_IF
  DTIG_END_FOR

  disp("Waiting for start");
  if ~waitForState([dtig.EState.WAITING, dtig.EState.RUNNING])
    return;
  end

  % Reset simulation for multiple runs
  if sm.Status ~= "inactive"
    terminate(sm);
  end

  disp("Starting the model")
  sm = setModelParameter(sm, ...
    StartTime=string(startTime), ...
    StopTime=string(stopTime), ...
    FixedStep=string(stepSize)...
  );

  % Make sure simulink stops once the simulation is done
  set_param(modelName, "StopFcn", "if status.state ~= dtig.EState.STOPPED status.state = dtig.EState.IDLE; end");

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

<DTIG_CALLBACK(SET_INPUT)>
function returnValue = set_input(reference, anyValue)
DTIG_IF(NOT DTIG_INPUTS)
  returnValue = createReturn(dtig.EReturnCode.DOES_NOT_EXIST, "Model has no inputs");
DTIG_ELSE
  global modelName;
  DTIG_FOR(DTIG_INPUTS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  handle = getSimulinkBlockHandle(strcat(modelName, "/", string(reference)), true);
  if handle < 0
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
    return;
  end

  value = dtig.Helpers.unpack(anyValue);
  if isempty(value)
    returnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));
    return;
  end

  % Update variable as well
  DTIG_FOR(DTIG_INPUTS)
  DTIG_IF(DTIG_INDEX == 0)
  if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_ELSE
  elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_END_IF
    DTIG_ITEM_NAME = value.getValue();
    set_param(handle, DTIG_TO_TYPE(DTIG_ITEM_TYPE), DTIG_STR(DTIG_ITEM_NAME));
  DTIG_END_FOR
  end
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
DTIG_END_IF
end

<DTIG_CALLBACK(SET_PARAMETER)>
function returnValue = set_parameter(reference, anyValue)
DTIG_IF(NOT DTIG_PARAMETERS)
  returnValue = createReturn(dtig.EReturnCode.DOES_NOT_EXIST, "Model has no parameters");
DTIG_ELSE
  global modelName;
  DTIG_FOR(DTIG_PARAMETERS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  handle = getSimulinkBlockHandle(strcat(modelName, "/", string(reference)), true);
  if handle < 0
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown parameter: ", reference));
    return;
  end

  value = dtig.Helpers.unpack(anyValue);
  if isempty(value)
    returnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));
    return;
  end

  % Update variable as well
  DTIG_FOR(DTIG_PARAMETERS)
  DTIG_IF(DTIG_INDEX == 0)
  if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_ELSE
  elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_END_IF
    DTIG_ITEM_NAME = value.getValue();
    set_param(handle, DTIG_TO_TYPE(DTIG_ITEM_TYPE), DTIG_STR(DTIG_ITEM_NAME));
  DTIG_END_FOR
  end
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
DTIG_END_IF
end

<DTIG_CALLBACK(GET_OUTPUT)>
function returnValue = get_output(references)
DTIG_IF(NOT DTIG_OUTPUTS)
  returnValue = createReturn(dtig.EReturnCode.DOES_NOT_EXIST, "Model has no outputs");
DTIG_ELSE
  global sm;
  DTIG_FOR(DTIG_OUTPUTS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  isRunning = (sm.Status == "running");

  if isRunning
    pause(sm);
  end

  dtigOutputs = dtig.MValues.newBuilder();
  nIds = references.size() - 1;
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);

  for i = 0:nIds
    reference = references.get(i);
    simulinkReference = find(sm.SimulationOutput, string(reference));
    if isempty(simulinkReference)
      continue
    end

    value = simulinkReference.Data(end);
    DTIG_FOR(DTIG_OUTPUTS)
    DTIG_IF(DTIG_INDEX == 0)
    if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_ELSE
    elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF
      anyValue = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE).newBuilder().setValue(value);
    DTIG_END_FOR
    else
      returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown output: ", reference));
      return;
    end
    dtigOutputs.addIdentifiers(reference);
    dtigOutputs.addValues(dtig.Helpers.pack(anyValue));
  end

  returnValue.setValues(dtigOutputs);

  if isRunning
    resume(sm);
  end
DTIG_END_IF
end

<DTIG_CALLBACK(GET_PARAMETER)>
function returnValue = get_parameter(references)
DTIG_IF(NOT DTIG_PARAMETERS)
  returnValue = createReturn(dtig.EReturnCode.DOES_NOT_EXIST, "Model has no parameters");
DTIG_ELSE
  global modelName;
  DTIG_FOR(DTIG_PARAMETERS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  dtigParameters = dtig.MValues.newBuilder();
  nIds = references.size() - 1;
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);

  for i = 0:nIds
    reference = references.get(i);
    handle = getSimulinkBlockHandle(strcat(modelName, "/", string(reference)), true);
    if handle < 0
      returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown parameter: ", reference));
      return;
    end

    DTIG_FOR(DTIG_PARAMETERS)

    DTIG_IF(DTIG_INDEX == 0)
    if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_ELSE
    elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF
    DTIG_IF(DTIG_ITEM_TYPE == DTIG_TYPE_STRING)
      param_value = get_param(handle, DTIG_TO_TYPE(DTIG_ITEM_TYPE));
    DTIG_ELSE
      param_value = eval(get_param(handle, DTIG_TO_TYPE(DTIG_ITEM_TYPE)));
    DTIG_END_IF
      anyValue = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE).newBuilder().setValue(param_value);
    DTIG_END_FOR
    else
      returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown output: ", reference));
      return;
    end
    dtigParameters.addIdentifiers(reference);
    dtigParameters.addValues(dtig.Helpers.pack(anyValue));
  end

  returnValue.setValues(dtigParameters);
DTIG_END_IF
end

<DTIG_CALLBACK(IMPORTS)>
global sm;

DTIG_IF(DTIG_INPUTS)
% Inputs
DTIG_FOR(DTIG_INPUTS)
global DTIG_ITEM_NAME;
DTIG_IF(HAS DTIG_ITEM_DEFAULT)
DTIG_ITEM_NAME = DTIG_ITEM_DEFAULT;
DTIG_END_IF
DTIG_END_FOR
DTIG_END_IF

DTIG_IF(DTIG_OUTPUTS)
% Outputs
DTIG_FOR(DTIG_OUTPUTS)
DTIG_IF(DTIG_ITEM_NAME IN DTIG_INPUTS_NAMES)
% Output DTIG_ITEM_NAME is also defined as in input
DTIG_ELSE
global DTIG_ITEM_NAME;
DTIG_IF(HAS DTIG_ITEM_DEFAULT)
DTIG_ITEM_NAME = DTIG_ITEM_DEFAULT;
DTIG_END_IF
DTIG_END_IF
DTIG_END_FOR
DTIG_END_IF

DTIG_IF(DTIG_PARAMETERS)
% Parameters
DTIG_FOR(DTIG_PARAMETERS)
global DTIG_ITEM_NAME;
DTIG_IF(HAS DTIG_ITEM_DEFAULT)
DTIG_ITEM_NAME = DTIG_ITEM_DEFAULT;
DTIG_END_IF
DTIG_END_FOR
DTIG_END_IF
