% @callback(imports)
global model_name;

% @callback(initialize)
function returnValue = initialize_callback()
  global state;
  global model_name;

  model_name = parse_and_assign_optional(message, "model_name")
  if self.model_name is None:
      return self.return_code(dtig_code.UNKNOWN_OPTION, f'No model provided')

  return dtig_return.MReturnValue(code=dtig_code.SUCCESS)
end