% @imports
% Clear the prompt
clc;

% Include jar paths
javaaddpath('./');
javaaddpath('./build');

% import states
import Status.*;

% Define global variables
global startTime stopTime stepSize;
global status modelName;

startTime = 0.0;
stopTime = 5.0;
stepSize = 0.001;

status = Status;
status.state = dtig.EState.UNINITIALIZED;
status.step = false;

% @states
classdef Status < handle
  properties
    state
    mode
    step
  end
  methods
    function set.state(obj, val)
        obj.state = val;
    end
    function ret = get.state(obj)
        ret = obj.state;
    end
    function set.step(obj, val)
      obj.step = val;
    end
    function ret = get.step(obj)
        ret = obj.step;
    end
    function set.mode(obj, val)
      obj.mode = val;
    end
    function ret = get.mode(obj)
        ret = obj.mode;
    end
  end
end

% @main
% ======================================================================
% Main
% ======================================================================
server = tcpserver("127.0.0.1", 8080, "ConnectionChangedFcn", @connectionFcn);

configureCallback(server, "byte", 5, @readByteFcn);

% start running in parallel
% start(dtig.ServerThread("127.0.0.1", 8080));

try
  disp("Server is running");
  % @>runmodel();

  disp("Model done, waiting for stop");
  waitfor(status, "state", dtig.EState.STOPPED);
  % pause
catch exception
  disp(getReport(exception));
end

disp("Server stopped");
clear server;

% ======================================================================
% Functions
% ======================================================================

% @method(public)
function connectionFcn(src, ~)
  if src.Connected
    disp("Client has connected")
  else
    disp("Client has disconnected.")
  end
end

% @method(public)
function readByteFcn(src, ~)
  if src.NumBytesAvailable < 1
    return
  end

  % Read data and process it as a protobuf object
  data = read(src, src.NumBytesAvailable);
  message = dtig.Helpers.parseFrom(data);
  try
    returnValue = % @>messagehandler(message);
  catch exception
    disp(getReport(exception));
    returnValue = createReturn(dtig.EReturnCode.FAILURE, "Exception when handling message");
  end

  % Send the reply
  write(src, dtig.Helpers.toByteArray(returnValue), "int8");
end

% @method(public)
function message = createReturn(code, errorMessage)
  message = dtig.MReturnValue.newBuilder();
  message.setCode(code);
  if (nargin == 2)
    message.setErrorMessage(dtig.MString.newBuilder().setValue(errorMessage));
  end
end

% @messagehandler
function returnValue = handleMessage(message)
  if message.hasStop()
    returnValue = % @>parse(stop)(message.getStop());
  elseif message.hasStart()
    returnValue = % @>parse(start)(message.getStart());
  elseif message.hasSetInput()
    returnValue = % @>parse(set_input)(message.getSetInput());
  elseif message.hasGetOutput()
    returnValue = % @>parse(get_output)(message.getGetOutput());
  elseif message.hasAdvance()
    returnValue = % @>parse(advance)(message.getAdvance());
  elseif message.hasInitialize()
    returnValue = % @>parse(initialize)(message.getInitialize());
  elseif message.hasSetParameter()
    returnValue = % @>parse(set_parameter)(message.getSetParameter());
  elseif message.hasGetParameter()
    returnValue = % @>parse(get_parameter)(message.getGetParameter());
  elseif message.hasGetStatus()
    returnValue = % @>parse(get_status)();
  else
    returnValue = % @>parse(model_info)();
  end
end

% @parse(initialize)
function returnValue = parse_initialize(message)
  global status;
  returnValue = % @>callback(initialize)(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS)
    return;
  end

  status.state = dtig.EState.INITIALIZED;
end

% @parse(start)
function returnValue = parse_start(message)
  global status;
  % If the model was not yet initialized, we cannot start
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot start while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(start)(message);
end

% @parse(stop)
function returnValue = parse_stop(message)
  global status;

  returnValue = % @>callback(stop)(message);
  if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
    return
  end

  status.step = true;
  status.state = dtig.EState.STOPPED;
end

% @parse(set_input)
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
    returnValue = % @>callback(set_input)(identifier, anyValue);
    if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
      return;
    end
  end
end

% @parse(set_parameter)
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
    returnValue = % @>callback(set_parameter)(identifier, anyValue);
    if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
      return;
    end
  end
end

% @parse(get_output)
function returnValue = parse_get_output(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get output while UNINITIALIZED");
    return;
  end

  nIds = message.getOutputs().getIdentifiersCount();
  returnValue = % @>callback(get_output)(message.getOutputs().getIdentifiersList());
  if returnValue.getValues().getIdentifiersCount() ~= nIds && returnValue.getCode() == dtig.EReturnCode.SUCCESS
    returnValue.setCode(dtig.EReturnCode.FAILURE);
    returnValue.setErrorMessage("Failed to get all parameters");
  end
end

% @parse(get_parameter)
function returnValue = parse_get_parameter(message)
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get parameter while UNINITIALIZED");
    return;
  end

  nIds = message.getParameters().getIdentifiersCount();
  returnValue = % @>callback(get_parameter)(message.getParameters().getIdentifiers());
  if returnValue.getValues().getIdentifiersSize() ~= nIds && returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
    returnValue.setCode(dtig.EReturnCode.FAILURE);
    returnValue.setErrorMessage("Failed to get all parameters");
  end
end

% @parse(advance)
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

  returnValue = % @>callback(advance)(message);
end

% @parse(model_info)
function returnValue = parse_model_info()
  global status;
  if (status.state == dtig.EState.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get model info while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(model_info)();
end

% @parse(get_status)
function returnValue = parse_get_status()
  returnValue = % @>callback(get_status)();
end

% @callback(initialize)
function returnValue = initialize_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support initialize call");
end

% @callback(advance)
function returnValue = advance_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support advance call");
end

% @callback(stop)
function returnValue = stop_callback(message)
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(start)
function returnValue = start_callback(message)
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support start call");
end

% @callback(model_info)
function returnValue = model_info_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support model_info call");
end

% @callback(set_input)
function returnValue = set_input_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support set_input call");
end

% @callback(get_output)
function returnValue = get_output_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support get_output call");
end

% @callback(set_parameter)
function returnValue = set_parameter_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support set_parameter call");
end

% @callback(get_parameter)
function returnValue = get_parameter_callback()
  returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, "Engine does not support get_parameter call");
end