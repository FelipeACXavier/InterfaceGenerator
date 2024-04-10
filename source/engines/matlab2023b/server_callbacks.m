% @callback(initialize)
function returnValue = initialize_callback(message)
  global status;
  global model_name;

  if message.hasModelName()
    modelName = message.getModelName().getValue();
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
  status.state = dtig.EState.RUNNING;

  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(stop)
function returnValue = parse_stop(~)
  returnValue = createReturn(dtig.EReturnCode.SUCCESS);
end

% @callback(advance)
function returnValue = parse_advance(message)
  global status;
  global stepSize;
  if message.hasStepSize()
    stepSize = message.getStepSize().getStep();
  end

  status.state = dtig.EState.RUNNING;
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
  global status;
  global h v;
  global startTime stopTime stepSize;

  disp("Waiting for initialization");
  waitfor(status, "state", dtig.EState.INITIALIZED);
  % Parameters
  g = 9.81;
  e = 0.7;

  % Inputs and outputs
  h = 1;
  v = 0;

  disp("Waiting for start");
  waitfor(status, "state", dtig.EState.RUNNING);

  if status.mode == dtig.ERunMode.STEPPED
    status.state = dtig.EState.WAITING;
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
      waitfor(status, "state", dtig.EState.RUNNING);
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

  status.state = dtig.EState.IDLE;

  % plot (t, y, "LineWidth", 1);
  % xlabel("Time (s)");
  % ylabel("Height (m)");
  % title("Bouncing ball simulation");
  % grid on
end