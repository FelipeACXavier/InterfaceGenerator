<DTIG_CALLBACK(INITIALIZE)>
function returnValue = initialize_callback(message)
  global status;
  global modelName;

  if message.hasModelName()
    modelName = string(message.getModelName().getValue());
    returnValue = createReturn(dtig.EReturnCode.SUCCESS);
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
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

<DTIG_CALLBACK(ADVANCE)>
function returnValue = parse_advance(message)
  global status;
  global stepSize;
  if message.hasStepSize()
    stepSize = message.getStepSize().getStep();
  end

  status.state = dtig.EState.RUNNING;
  status.wait = false;
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
  global status;
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

  fprintf("Starting with: %s\n", string(status.state));
  fprintf("Running from %.4f to %.4f with step size %.4f\n", startTime, stopTime, stepSize);

  t = startTime:stepSize:stopTime;
  y = zeros(size(t));
  x = zeros(size(t));
  dt = stepSize;

  % Set initial values
  y(1) = h;
  x(1) = v;

  % Run model
  for i = 2:length(t)
    if status.state == dtig.EState.STOPPED
      break
    elseif status.mode == dtig.ERunMode.STEPPED
      if ~waitForState([dtig.EState.RUNNING])
        break
      end
    end

    if y(i - 1) <= 0 && x(i - 1) < 0
        x(i) = -e * x(i - 1);
        y(i) = 0;
    else
        x(i) = x(i - 1) - g*dt;
        y(i) = y(i - 1) + x(i - 1)*dt - (0.5*g*dt^2);
    end

    % Update outputs
    h = y(i);
    v = x(i);

    if status.mode == dtig.ERunMode.STEPPED
      status.state = dtig.EState.WAITING;
    end
  end

  if status.state ~= dtig.EState.STOPPED
    status.state = dtig.EState.IDLE;
  end

  plot (t, y, "LineWidth", 1);
  xlabel("Time (s)");
  ylabel("Height (m)");
  title("Bouncing ball simulation");
  grid on
end

<DTIG_CALLBACK(SET_INPUT)>
function returnValue = set_inputs(reference, anyValue)
  DTIG_IF(NOT DTIG_INPUTS_LENGTH)
  returnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no inputs");
  return;
  DTIG_ELSE

  DTIG_FOR(DTIG_INPUTS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  % Check that the reference is valid
  value = dtig.Helpers.unpack(anyValue);
  if isempty(value)
    returnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));
    return;
  end

  DTIG_FOR(DTIG_INPUTS)

  DTIG_IF(DTIG_INDEX == 0)
  if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_ELSE
  elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_END_IF
    DTIG_ITEM_NAME = value.getValue();
  DTIG_END_FOR
  else
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
    return;
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end
DTIG_END_IF

<DTIG_CALLBACK(SET_PARAMETER)>
function returnValue = set_parameter(reference, anyValue)
  DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
  returnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no parameters");
  return;
  DTIG_ELSE

  DTIG_FOR(DTIG_PARAMETERS)
  global DTIG_ITEM_NAME;
  DTIG_END_FOR

  % Check that the reference is valid
  value = dtig.Helpers.unpack(anyValue);
  if isempty(value)
    returnValue = createReturn(dtig.EReturnCode.FAILURE, strcat("Failed to unpack value: ", reference));
    return;
  end

  DTIG_FOR(DTIG_PARAMETERS)

  DTIG_IF(DTIG_INDEX == 0)
  if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_ELSE
  elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
  DTIG_END_IF
    DTIG_ITEM_NAME = value.getValue();
  DTIG_END_FOR
  else
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
    return;
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end
DTIG_END_IF

<DTIG_CALLBACK(GET_OUTPUT)>
function returnValue = get_outputs(references)
DTIG_IF(NOT DTIG_OUTPUTS_LENGTH)
  returnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no outputs");
  return;
DTIG_ELSE

DTIG_FOR(DTIG_OUTPUTS)
  global DTIG_ITEM_NAME;
DTIG_END_FOR

  dtigOutputs = dtig.MValues.newBuilder();
  nIds = references.size() - 1;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  for i = 0:nIds
    reference = references.get(i);
    dtigOutputs.addIdentifiers(reference);

    DTIG_FOR(DTIG_OUTPUTS)
    DTIG_IF(DTIG_INDEX == 0)
    if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_ELSE
    elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF
      anyValue = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE).newBuilder().setValue(DTIG_ITEM_NAME);
    DTIG_END_FOR
    else
      returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
      return;
    end

    dtigOutputs.addValues(dtig.Helpers.pack(anyValue));
  end

  returnValue.setValues(dtigOutputs);
end
DTIG_END_IF

<DTIG_CALLBACK(GET_PARAMETER)>
function returnValue = get_outputs(references)
DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
  returnValue = createReturn(dtig.EReturnCode.FAILURE, "Model has no parameters");
  return;
DTIG_ELSE

DTIG_FOR(DTIG_PARAMETERS)
  global DTIG_ITEM_NAME;
DTIG_END_FOR

  dtigParameters = dtig.MValues.newBuilder();
  nIds = references.size() - 1;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  for i = 0:nIds
    reference = references.get(i);
    dtigParameters.addIdentifiers(reference);

    DTIG_FOR(DTIG_PARAMETERS)
    DTIG_IF(DTIG_INDEX == 0)
    if string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_ELSE
    elseif string(reference) == DTIG_STR(DTIG_ITEM_NAME)
    DTIG_END_IF
      anyValue = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE).newBuilder().setValue(DTIG_ITEM_NAME);
    DTIG_END_FOR
    else
      returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, strcat("Unknown input: ", reference));
      return;
    end

    dtigParameters.addValues(dtig.Helpers.pack(anyValue));
  end

  returnValue.setValues(dtigParameters);
end
DTIG_END_IF

<DTIG_CALLBACK(IMPORTS)>
DTIG_IF(DTIG_INPUTS_LENGTH)

% Inputs
DTIG_FOR(DTIG_INPUTS)
global DTIG_ITEM_NAME;
DTIG_IF(HAS DTIG_ITEM_DEFAULT)
DTIG_ITEM_NAME = DTIG_ITEM_DEFAULT;
DTIG_END_IF
DTIG_END_FOR
DTIG_END_IF

DTIG_IF(DTIG_OUTPUTS_LENGTH)

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

DTIG_IF(DTIG_PARAMETERS_LENGTH)

% Parameters
DTIG_FOR(DTIG_PARAMETERS)
global DTIG_ITEM_NAME;
DTIG_IF(HAS DTIG_ITEM_DEFAULT)
DTIG_ITEM_NAME = DTIG_ITEM_DEFAULT;
DTIG_END_IF
DTIG_END_FOR
DTIG_END_IF
