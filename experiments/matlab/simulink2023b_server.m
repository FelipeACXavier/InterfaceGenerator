% Clear the prompt
clc;

% Include jar paths
javaaddpath('./protobuf-java-3.20.3.jar');
javaaddpath('./build/dtig.jar');

import State.*;

% Define global variables
global step;
global state;

step = false;
state = State.UNINITIALIZED;

% ======================================================================
% Main
% ======================================================================
% t = tcpserver("127.0.0.1", 8080, "ConnectionChangedFcn", @connectionFcn);
% 
% configureCallback(t, "byte", 5, @readByteFcn);

msg = dtig.MAdvance.newBuilder() ...
    .setStepSize(dtig.MStep.newBuilder() ...
        .setStep(dtig.MNumber64.newBuilder() ...
            .setFvalue(dtig.MF64.newBuilder() ...
                .setValue(0.05)))).build();

% a = javaMethod('newBuilder', 'protobuf.Advance$MAdvance');
% s = msg.getStepSize();
disp(msg.getStepSize().getStep().getFvalue().getValue());

% Wait until the user presses enter and then clean the server
% pause
% clear t;
disp("A more complicated message creation");
inputs = dtig.MValues.newBuilder();

% Add identifiers
identifiers = dtig.MIdentifiers.newBuilder()...
  .setNames(dtig.MNames.newBuilder()...
      .addNames("h")).build();

inputs.setIdentifiers(identifiers);

% Add values
inputs.addValues(com.google.protobuf.Any.pack(dtig.MF64.newBuilder()...
    .setValue(0.8).build()));

inputs.addValues(com.google.protobuf.Any.pack(dtig.MF64.newBuilder()...
    .setValue(0.9).build()));

inputs.addValues(com.google.protobuf.Any.pack(dtig.MF64.newBuilder()...
    .setValue(1.0).build()));

input = dtig.MInput.newBuilder()...
  .setInputs(inputs.build())...
  .build();

disp(input.toString());

disp("Unpacking values");
vals = input.getInputs().getValuesList();
for i = 0:vals.size() - 1
    item = vals.get(i);
    disp(dtig.Helpers.unpack(item).getValue());
end

disp(dtig.EReturnCode.SUCCESS);

init = dtig.MInitialize.newBuilder();
init.setModelName(dtig.MString.newBuilder() ...
    .setValue("MyModelName"));

fields = init.getFields();
for field = fields
    disp(field.getName());
    if field.getName() == "model_name"
        disp("Message has field")
        break
    end
end

% t = tcpserver("127.0.0.1", 8080, "ConnectionChangedFcn", @connectionFcn);
% 
% configureCallback(t, "byte", 5, @readByteFcn);
% 
% pause
% clear t;

% ======================================================================
% Functions
% ======================================================================
function connectionFcn(src, ~)
  if src.Connected
    disp("Client has connected")
  else
    disp("Client has disconnected.")
  end
end

function readByteFcn(src, ~)
  if src.NumBytesAvailable < 1
    return
  end

  % Read data and process it as a protobuf object
  data = read(src, src.NumBytesAvailable);
  message = dti.ProtoWrapper.parseFrom(data);
  returnValue = handle_message(message);

  % Send the reply
  write(src, returnValue.toByteArray(b));
end

function message = createReturn(code, errorMessage)
  message = dti.MyProto.newBuilder();
  message.setCode(code);
  if (nargin == 2)
    message.setMessage(errorMessage);
  end
end

function returnValue = handle_message(message)
  if message.HasField("stop")
    returnValue = parse_stop(message.stop);
  elseif message.HasField("start")
    returnValue = parse_start(message.start);
  elseif message.HasField("input")
    returnValue = parse_set_input(message.input.inputs);
  elseif message.HasField("output")
    returnValue = parse_get_output(message.output.outputs);
  elseif message.HasField("advance")
    returnValue = parse_advance(message.advance);
  elseif message.HasField("initialize")
    returnValue = parse_initialize(message.initialize);
  else
    returnValue = parse_model_info();
  end
end

function returnValue = parse_stop(message)
  global step;
  global state;
  returnValue = stop_callback(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS);
    return;
  end

  step = True;
  state = State.STOPPED;
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

function returnValue = parse_start(message)
  global state;
  % If the model was not yet initialized, we cannot start
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot start while UNINITIALIZED");
    return;
  end

  returnValue = start_callback(message);
end

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
        returnValue = set_input_callback(identifier, value.getValue());
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
    values = get_output_callback(names);
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

function returnValue = parse_advance(message)
  global state;
  if (state ~= State.STEPPING)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, 'Cannot advance, not in STEPPING state');
    return;
  end

  returnValue = advance_callback(message);
end

function returnValue = parse_initialize(message)
  global state;
  returnValue = initialize_callback(message);
  if (returnValue.getCode() ~= dtig.EReturnCode.SUCCESS)
    return;
  end

  state = State.INITIALIZING;
end

function returnValue = parse_model_info()
  global state;
  if (state == State.UNINITIALIZED)
    returnValue = createReturn(dtig.EReturnCode.INVALID_STATE, "Cannot get model info while UNINITIALIZED");
    return;
  end

  returnValue = model_info_callback();
end
