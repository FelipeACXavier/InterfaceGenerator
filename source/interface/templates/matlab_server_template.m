% @imports
% Clear the prompt
clc;

% Include jar paths
javaaddpath('./');
javaaddpath('./build');

% Define global variables
global step;
global state;

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
  returnValue = % @>messagehandler(message)

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
  returnValue = % @>callback(initialize)();
  if (returnValue.getCode() ~= dtig_code.SUCCESS)
    return;
  end

  state = State.INITIALIZING
end

% @parse(start)
function returnValue = parse_start(message)
  global state;
  % If the model was not yet initialized, we cannot start
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig_code.INVALID_STATE, "Cannot start while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(start)(message);
end

% @parse(stop)
function returnValue = parse_stop(message)
  global step;
  global state;
  returnValue = % @>callback(stop)(message);
  if (returnValue.getCode() ~= dtig_code.SUCCESS)
    return;
  end

  step = True;
  state = State.STOPPED;
  returnValue = createReturn(dtig_code.SUCCESS)
end

% @parse(setinput)
function returnValue = parse_set_input(message)
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig_code.INVALID_STATE, "Cannot set input while UNINITIALIZED");
    return
  end

  returnValue = createReturn(dtig_code.SUCCESS)
  if (message.getIdentifiers().HasField("names"))
    n_inputs = length(message.getIdentifiers().getNames().getNames())
    for i = 1:n_inputs
      identifier = message.getIdentifiers().getNames().getNames(i);
      value = message.getValues(i);
      fval = value.Unpack(fval);
      if fval
        returnValue = % @>callback(setinput)(identifier, fval.value);
        if returnValue.getCode() ~= dtig_code.SUCCESS
          return;
        end
      else
        returnValue = createReturn(dtig_code.INVALID_OPTION, 'Non-float values not yet supported');
        return;
      end
    end
  elseif message.identifiers.HasField("ids")
    returnValue = createReturn(dtig_code.UNKNOWN_OPTION, 'Non-string ids not implemented')
  else
    returnValue = createReturn(dtig_code.INVALID_OPTION, "No identifiers provided");
  end
end

% @parse(getoutput)
function returnValue = parse_get_output(message)
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig_code.INVALID_STATE, "Cannot get output while UNINITIALIZED");
    return;
  end

  returnValue = createReturn(dtig_code.SUCCESS);
  if (message.getIdentifiers().HasField("names"))
    names = message.getIdentifiers().getNames().getNames();
    n_outputs = lenght(names);
    values = % @>callback(getoutput)(names);
    if length(values) ~= n_outputs
      returnValue = createReturn(dtig_code.FAILURE, 'Failed to get all outputs');
      return
    end

    returnValue = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    for i = 1:n_outputs
      returnValue.values.identifiers.names.names.append(names[i])

      %  Set the output value
      value = dti.MF32.newBuilder();
      value.setValue(values[i])
      s = dti.MyProto.pack(value);
      return_value.getValues().getValues().Append(any_msg);
    end
  elseif message.identifiers.HasField("ids")
    returnValue = createReturn(dtig_code.UNKNOWN_OPTION, 'Non-string ids not implemented');
  else
    returnValue = createReturn(dtig_code.INVALID_OPTION, 'No identifiers provided');
  end
end

% @parse(advance)
function returnValue = parse_advance(message)
  global state;
  if (state ~= State.STEPPING)
    returnValue = createReturn(dtig_code.INVALID_STATE, 'Cannot advance, not in STEPPING state');
    return;
  end

  createReturn = % @>callback(advance)(message);
end

% @parse(modelinfo)
function returnValue = parse_model_info()
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig_code.INVALID_STATE, "Cannot get model info while UNINITIALIZED");
    return;
  end

  returnValue = % @>callback(modelinfo)();
end