% @imports
% Clear the prompt
clc;

% Include jar paths
javaaddpath('./');
javaaddpath('./build');

% import states
import State.*;

% Define global variables
global step;
global state;

step = false;
state = State.UNINITIALIZED;

% @states
classdef State
  enumeration
    UNINITIALIZED,
    INITIALIZING,
    IDLE,
    RUNNING,
    STEPPING,
    STOPPED
  end
end

% @main
% ======================================================================
% Main
% ======================================================================
t = tcpserver("127.0.0.1", 8080, "ConnectionChangedFcn", @connectionFcn);

configureCallback(t, "byte", 5, @readByteFcn);

% Wait until the user presses enter and then clean the server
pause
clear t;

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
  message = dti.ProtoWrapper.parseFrom(data);
  returnValue = % @>messagehandler(message);

  % Send the reply
  write(src, returnValue.toByteArray(b));
end

% @method(public)
function message = createReturn(code, errorMessage)
  message = dti.MyProto.newBuilder();
  message.setCode(code);
  if (nargin == 2)
    message.setMessage(errorMessage);
  end
end

% @messagehandler
function returnValue = handleMessage(message)
  if message.HasField("stop")
    returnValue = % @>parse(stop)(message.stop);
  elseif message.HasField("start")
    returnValue = % @>parse(start)(message.start);
  elseif message.HasField("input")
    returnValue = % @>parse(setinput)(message.input.inputs);
  elseif message.HasField("output")
    returnValue = % @>parse(getoutput)(message.output.outputs);
  elseif message.HasField("advance")
    returnValue = % @>parse(advance)(message.advance);
  elseif message.HasField("initialize")
    returnValue = % @>parse(initialize)(message.initialize);
  else
    returnValue = % @>parse(modelinfo)();
  end
end

% @parse(initialize)
function returnValue = parse_initialize(message)
  global state;
  returnValue = % @>callback(initialize)(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS)
    return;
  end

  state = State.INITIALIZING;
end

% @parse(start)
function returnValue = parse_start(message)
  global state;
  % If the model was not yet initialized, we cannot start
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot start while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(start)(message);
end

% @parse(stop)
function returnValue = parse_stop(message)
  global step;
  global state;
  returnValue = % @>callback(stop)(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS)
    return;
  end

  step = True;
  state = State.STOPPED;
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @parse(setinput)
function returnValue = parse_set_input(message)
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot set input while UNINITIALIZED");
    return
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  if (message.getIdentifiers().HasField("names"))
    n_inputs = message.getIdentifiers().getNames().getNames().size();
    for i = 1:n_inputs
      identifier = message.getIdentifiers().getNames().getNames(i);
      value = dtig.Helpers.unpack(message.getValues(i));
      if value
        returnValue = % @>callback(setinput)(identifier, value.getValue());
        if returnValue.getCode() ~= dtig.EReturnCode.SUCCESS
          return;
        end
      else
        returnValue = createReturn(dtig.EReturnCode.INVALID_OPTION, 'Could not unpack value');
        return;
      end
    end
  elseif message.getIdentifiers().HasField("ids")
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, 'Non-string ids not implemented');
  else
    returnValue = createReturn(dtig.EReturnCode.INVALID_OPTION, "No identifiers provided");
  end
end

% @parse(getoutput)
function returnValue = parse_get_output(message)
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get output while UNINITIALIZED");
    return;
  end

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
  if (message.getIdentifiers().HasField("names"))
    names = message.getIdentifiers().getNames().getNames();
    n_outputs = names.size();
    values = % @>callback(getoutput)(names);
    if values.size() ~= n_outputs
      returnValue = createReturn(dtig.EReturnCode.FAILURE, 'Failed to get all outputs');
      return
    end

    outputs = dtig.MValues.newBuilder();
    names = dtig.MNames.newBuilder();
    for i = 1:n_outputs
      names.addNames(names.get(i));

      %  Set the output value
      outputs.addValues(com.google.protobuf.Any...
        .pack(dtig.MF32.newBuilder()...
          .setValue(values.get(i)).build()));
    end

    outputs.setIdentifiers(...
      dtig.MIdentifiers.newBuilder()...
        .setNames(names));

    returnValue.setValues(outputs.build());

  elseif message.getIdentifiers().HasField("ids")
    returnValue = createReturn(dtig.EReturnCode.UNKNOWN_OPTION, 'Non-string ids not implemented');
  else
    returnValue = createReturn(dtig.EReturnCode.INVALID_OPTION, 'No identifiers provided');
  end
end

% @parse(advance)
function returnValue = parse_advance(message)
  global state;
  if (state ~= State.STEPPING)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, 'Cannot advance, not in STEPPING state');
    return;
  end

  returnValue = % @>callback(advance)(message);
end

% @parse(modelinfo)
function returnValue = parse_model_info()
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get model info while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(modelinfo)();
end