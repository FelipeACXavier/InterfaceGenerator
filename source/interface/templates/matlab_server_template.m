<DTIG_IMPORTS>
% Clear the prompt
clc;

% Include jar paths
javaaddpath('./');
javaaddpath('./build');

% import states
import Status.*;

% Define global variables
global status modelName;
global startTime stopTime stepSize simulationTime;

startTime = 0.0;
stopTime = 0.0;
stepSize = 0.001;

status = Status;
status.wait = true;
status.state = dtig.EState.UNINITIALIZED;
status.mode = dtig.ERunMode.UNKNOWN;

<DTIG_STATES>
classdef Status < handle
  properties
    state
    mode
    wait
  end
  methods
    function set.state(obj, val)
        obj.state = val;
    end
    function ret = get.state(obj)
        ret = obj.state;
    end
    function set.wait(obj, val)
      obj.wait = val;
    end
    function ret = get.wait(obj)
        ret = obj.wait;
    end
    function set.mode(obj, val)
      obj.mode = val;
    end
    function ret = get.mode(obj)
        ret = obj.mode;
    end
  end
end

<DTIG_MAIN>
% ======================================================================
% Main
% ======================================================================
server = tcpserver("127.0.0.1", 8080, "ConnectionChangedFcn", @connectionFcn);

configureCallback(server, "byte", 4, @readByteFcn);

try
  disp("Server is running");

  disp("Waiting for initialization");
  if ~waitForState([dtig.EState.INITIALIZED])
    return
  end

  while status.state ~= dtig.EState.STOPPED
    DTIG>RUNMODEL();
    disp("Model done, waiting for stop");
  end
catch exception
  disp(getReport(exception));
end

disp("Server stopped");
clear server;

% ======================================================================
% Functions
% ======================================================================

<DTIG_METHOD(PUBLIC)>
function connectionFcn(src, ~)
  if src.Connected
    disp("Client has connected")
  else
    disp("Client has disconnected.")
  end
end

<DTIG_METHOD(PUBLIC)>
function readByteFcn(src, ~)
  if src.NumBytesAvailable < 1
    return
  end

  % Read data and process it as a protobuf object
  data = read(src, src.NumBytesAvailable);
  message = dtig.Helpers.parseFrom(data);
  try
    returnValue = DTIG>MESSAGEHANDLER(message);
  catch exception
    disp(getReport(exception));
    returnValue = createReturn(dtig.EReturnCode.FAILURE, "Exception when handling message");
  end

  % Send the reply
  write(src, dtig.Helpers.toByteArray(returnValue), "int8");
end

<DTIG_METHOD(PUBLIC)>
function message = createReturn(code, errorMessage)
  message = dtig.MReturnValue.newBuilder();
  message.setCode(code);
  if (nargin == 2)
    message.setErrorMessage(dtig.MString.newBuilder().setValue(errorMessage));
  end
end

<DTIG_METHOD(PUBLIC)>
function returnValue = waitForState(expectedStates)
  global status;

  while ~ismember(string(status.state), string(expectedStates))
    waitfor(status, "wait", false);
    status.wait = true;
    if status.state == dtig.EState.STOPPED
      returnValue = false;
      return
    end
  end

  returnValue = true;
end

<DTIG_MESSAGEHANDLER>
function returnValue = handleMessage(message)
  if message.hasStop()
    returnValue = DTIG>PARSE(STOP)(message.getStop());
  elseif message.hasStart()
    returnValue = DTIG>PARSE(START)(message.getStart());
  elseif message.hasSetInput()
    returnValue = DTIG>PARSE(SET_INPUT)(message.getSetInput());
  elseif message.hasGetOutput()
    returnValue = DTIG>PARSE(GET_OUTPUT)(message.getGetOutput());
  elseif message.hasAdvance()
    returnValue = DTIG>PARSE(ADVANCE)(message.getAdvance());
  elseif message.hasInitialize()
    returnValue = DTIG>PARSE(INITIALIZE)(message.getInitialize());
  elseif message.hasSetParameter()
    returnValue = DTIG>PARSE(SET_PARAMETER)(message.getSetParameter());
  elseif message.hasGetParameter()
    returnValue = DTIG>PARSE(GET_PARAMETER)(message.getGetParameter());
  elseif message.hasGetStatus()
    returnValue = DTIG>PARSE(GET_STATUS)();
  else
    returnValue = DTIG>PARSE(MODEL_INFO)();
  end
end

<DTIG_PARSE(INITIALIZE)>
function returnValue = parse_initialize(message)
  global status;
  returnValue = DTIG>CALLBACK(INITIALIZE)(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS)
    return;
  end

  status.state = dtig.EState.INITIALIZED;
  status.wait = false;
end

<DTIG_PARSE(START)>
function returnValue = parse_start(message)
  global status;
  % If the model was not yet initialized, we cannot start
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot start while UNINITIALIZED");
    return;
  end

  returnValue = DTIG>CALLBACK(START)(message);
end

<DTIG_PARSE(STOP)>
function returnValue = parse_stop(message)
  global status;

  returnValue = DTIG>CALLBACK(STOP)(message);
  if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
    return
  end

  status.state = dtig.EState.STOPPED;
  status.wait = false;
end

<DTIG_PARSE(SET_INPUT)>
function returnValue = parse_set_input(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot set input while UNINITIALIZED");
    return
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  nIds = message.getInputs().getIdentifiersCount() - 1;
  for i = 0:nIds
    identifier = string(message.getInputs().getIdentifiers(i));
    anyValue = message.getInputs().getValues(i);
    returnValue = DTIG>CALLBACK(SET_INPUT)(identifier, anyValue);
    if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
      return;
    end
  end
end

<DTIG_PARSE(SET_PARAMETER)>
function returnValue = parse_set_parameter(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot set parameter while UNINITIALIZED");
    return
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  nIds = message.getParameters().getIdentifiersCount() - 1;
  for i = 0:nIds
    identifier = message.getParameters().getIdentifiers(i);
    anyValue = message.getParameters().getValues(i);
    returnValue = DTIG>CALLBACK(SET_PARAMETER)(identifier, anyValue);
    if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
      return;
    end
  end
end

<DTIG_PARSE(GET_OUTPUT)>
function returnValue = parse_get_output(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get output while UNINITIALIZED");
    return;
  end

  nIds = message.getOutputs().getIdentifiersCount();
  returnValue = DTIG>CALLBACK(GET_OUTPUT)(message.getOutputs().getIdentifiersList());
  if returnValue.getValues().getIdentifiersCount() ~= nIds && returnValue.getCode() == dtig.EReturnCode.SUCCESS
    returnValue.setCode(dtig.EReturnCode.FAILURE);
    returnValue.setErrorMessage("Failed to get all parameters");
  end
end

<DTIG_PARSE(GET_PARAMETER)>
function returnValue = parse_get_parameter(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get parameter while UNINITIALIZED");
    return;
  end

  nIds = message.getParameters().getIdentifiersCount();
  returnValue = DTIG>CALLBACK(GET_PARAMETER)(message.getParameters().getIdentifiers());
  if returnValue.getValues().getIdentifiersSize() ~= nIds && returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
    returnValue.setCode(dtig.EReturnCode.FAILURE);
    returnValue.setErrorMessage("Failed to get all parameters");
  end
end

<DTIG_PARSE(ADVANCE)>
function returnValue = parse_advance(message)
  global status;
  if status.mode ~= dtig.ERunMode.STEPPED
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, 'Cannot advance, not in STEPPING mode');
    return;
  end

  if status.state ~= dtig.EState.WAITING
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, 'Cannot advance, still running');
    return;
  end

  returnValue = DTIG>CALLBACK(ADVANCE)(message);
end

<DTIG_PARSE(MODEL_INFO)>
function returnValue = parse_model_info()
  returnValue = DTIG>CALLBACK(MODEL_INFO)();
end

<DTIG_PARSE(GET_STATUS)>
function returnValue = parse_get_status()
  returnValue = DTIG>CALLBACK(GET_STATUS)();
end

<DTIG_CALLBACK(INITIALIZE)>
function returnValue = initialize_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support initialize call");
end

<DTIG_CALLBACK(ADVANCE)>
function returnValue = advance_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support advance call");
end

<DTIG_CALLBACK(STOP)>
function returnValue = stop_callback(message)
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

<DTIG_CALLBACK(START)>
function returnValue = start_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support start call");
end

<DTIG_CALLBACK(MODEL_INFO)>
function returnValue = model_info_callback(message)
    returnValue = createReturn(dtig.EReturnCode.SUCCESS)

    dtigModelInfo = dtig.MModelInfo.newBuilder();

    % Inputs
    DTIG_FOR(DTIG_INPUTS)
    info_DTIG_ITEM_NAME = dtig.MInfo.newBuilder();

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME...
      .setId(dtig.MU32.newBuilder()...
        .setValue(DTIG_ITEM_ID))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME...
      .setName(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAME)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME...
      .setDescription(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DESCRIPTION)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME...
      .setType(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_TYPE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME...
      .setUnit(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_UNIT)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME...
      .setNamespace(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAMESPACE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME...
      .setDefault(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DEFAULT)))
    DTIG_END_IF

    dtigModelInfo.addInputs(info_DTIG_ITEM_NAME);
    DTIG_END_FOR

    % Outputs
    DTIG_FOR(DTIG_OUTPUTS)
    info_DTIG_ITEM_NAME = dtig.MInfo.newBuilder();

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME...
      .setId(dtig.MU32.newBuilder()...
        .setValue(DTIG_ITEM_ID))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME...
      .setName(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAME)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME...
      .setDescription(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DESCRIPTION)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME...
      .setType(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_TYPE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME...
      .setUnit(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_UNIT)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME...
      .setNamespace(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAMESPACE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME...
      .setDefault(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DEFAULT)))
    DTIG_END_IF

    dtigModelInfo.addOutputs(info_DTIG_ITEM_NAME);
    DTIG_END_FOR

    % Parameters
    DTIG_FOR(DTIG_PARAMETERS)
    info_DTIG_ITEM_NAME = dtig.MInfo.newBuilder();

    DTIG_IF(HAS DTIG_ITEM_ID)
    info_DTIG_ITEM_NAME...
      .setId(dtig.MU32.newBuilder()...
        .setValue(DTIG_ITEM_ID))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAME)
    info_DTIG_ITEM_NAME...
      .setName(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAME)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DESCRIPTION)
    info_DTIG_ITEM_NAME...
      .setDescription(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DESCRIPTION)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_TYPE)
    info_DTIG_ITEM_NAME...
      .setType(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_TYPE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_UNIT)
    info_DTIG_ITEM_NAME...
      .setUnit(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_UNIT)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_NAMESPACE)
    info_DTIG_ITEM_NAME...
      .setNamespace(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_NAMESPACE)))
    DTIG_END_IF

    DTIG_IF(HAS DTIG_ITEM_DEFAULT)
    info_DTIG_ITEM_NAME...
      .setDefault(dtig.MString.newBuilder()...
        .setValue(DTIG_STR(DTIG_ITEM_DEFAULT)))
    DTIG_END_IF

    dtigModelInfo.addParameters(info_DTIG_ITEM_NAME);
    DTIG_END_FOR

    returnValue.setModelInfo(dtigModelInfo)
end

<DTIG_CALLBACK(SET_INPUT)>
function returnValue = set_input_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support set_input call");
end

<DTIG_CALLBACK(GET_OUTPUT)>
function returnValue = get_output_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support get_output call");
end

<DTIG_CALLBACK(SET_PARAMETER)>
function returnValue = set_parameter_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support set_parameter call");
end

<DTIG_CALLBACK(GET_PARAMETER)>
function returnValue = get_parameter_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support get_parameter call");
end