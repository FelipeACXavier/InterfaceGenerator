<DTIG_CALLBACK(IMPORTS)>
FREECADPATH = '/usr/lib/freecad-python3/lib/'
FREECADFEMPATH = '/usr/lib/freecad/Mod/Fem/'
FREECADPYSIDEPATH = '/usr/share/freecad/Ext/'
DISTPACKAGESPATH = '/usr/lib/python3/dist-packages/'

import re
import sys
sys.path.append(FREECADPATH)
sys.path.append(FREECADFEMPATH)
sys.path.append(FREECADPYSIDEPATH)
sys.path.append(DISTPACKAGESPATH)

import FreeCAD, FreeCADGui, Part
import ObjectsFem

<DTIG_CLASSNAME>
FreeCADWrapper

<DTIG_CALLBACK(CONSTRUCTOR)>
# Engine specific members
self.stop_time  : float  = 10.0
self.step_size  : float  = 1e-3
self.model_name : str = None

self.app = None

self.solver = None
self.results = None
self.box_object = None
self.mesh_object = None
self.analysis_object = None

<DTIG_CALLBACK(INITIALIZE)>
def parse_initialize(message) -> Message:
    if not message.HasField("model_name"):
        return self.return_code(dtig_code.INVALID_OPTION, f'No model provided')

    self.model_name = message.model_name.value
    try:
        self.app = FreeCAD.open(self.model_name)

        print(f'Running with file: {self.model_name}')

        # Check if an analysis object already exists
        create_analysis = True
        for obj in self.app.Objects:
            if obj.isDerivedFrom('Fem::FemAnalysis'):
                print("Using existing analysis")
                self.analysis_object = obj
                create_analysis = False
                break

        # Otherwise, create a new one
        if create_analysis:
            print("Adding new analysis")
            self.analysis_object = ObjectsFem.makeAnalysis(self.app)

    except Exception as e:
        return self.return_code(dtig_code.FAILURE, f'{e}')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(START)>
def parse_start(message) -> Message:
    if message.HasField("stop_time"):
        self.stop_time = message.stop_time.value

    if message.HasField("step_size"):
        # TODO: Add support for micro steps
        self.step_size = message.step_size.step

    # For now, we accept either continuous or stepped simulation
    if message.run_mode == dtig_run_mode.UNKNOWN:
        return self.return_code(dtig_code.INVALID_OPTION, f'Unknown run mode: {message.run_mode}')

    self.mode = message.run_mode
    self.state = dtig_state.WAITING if self.mode == dtig_run_mode.STEPPED else dtig_state.RUNNING

    if not self.analysis_object:
        return self.return_code(dtig_code.INVALID_OPTION, f'Model not yet initialized')

    create_solver = True
    for obj in self.app.Objects:
        if obj.isDerivedFrom('Fem::FemSolverObjectPython'):
            print("Using existing solver")
            self.solver = obj
            create_solver = False
            break

    # Otherwise, create a new one
    if create_solver:
        print("Adding new solver")
        self.solver = ObjectsFem.makeSolverCalculixCcxTools(self.app)

    self.solver.GeometricalNonlinearity = 'linear'
    self.solver.ThermoMechSteadyState = True
    self.solver.MatrixSolverType = 'default'
    self.solver.IterationsControlParameterTimeUse = False
    self.solver.TimeInitialStep = self.step_size
    self.solver.TimeEnd = self.stop_time

    if create_solver:
        self.analysis_object.addObject(self.solver)

    self.mesh_object = self.get_object("MainMesh")
    if not self.mesh_object:
        print("No MainMesh found, adding a new one")
        self.mesh_object = ObjectsFem.makeMeshGmsh(self.app, "MainMesh")

        mesh_part = self.get_object("MainBody")
        if not mesh_part:
            return self.return_code(dtig_code.INVALID_OPTION, f'Could not find part: {"MainBody"}')

        self.mesh_object.Part = mesh_part

    # Here we just compute the mesh using the desired algorithm
    from femmesh.gmshtools import GmshTools

    print("Computing mesh")
    gmsh_mesh = GmshTools(self.mesh_object)
    error = gmsh_mesh.create_mesh()
    if error:
        return dtig_return.MReturnValue(code=dtig_code.FAILURE, message=f'GMESH error: {error}')

    self.analysis_object.addObject(self.mesh_object)
    self.app.save()

    print(f'Starting with: {dtig_run_mode.ERunMode.Name(self.mode)}.')
    print(f'Running {self.stop_time:0.4f} with {self.step_size:0.4f}')

    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(STOP)>
def parse_stop(message) -> Message:
    print(f'Stopping with: {message.mode}')
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

<DTIG_CALLBACK(ADVANCE)>
def parse_advance(self, message) -> Message:
    if message.HasField("step_size"):
        self.step_size = message.step_size.step

    self.state = dtig_state.RUNNING
    return self.return_code(dtig_code.SUCCESS)

<DTIG_CALLBACK(GET_STATUS)>
def parse_get_status() -> Message:
    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    return_value.status.state = self.state
    return return_value

<DTIG_METHOD(PUBLIC)>
def variable_to_info(variable):
    info = dtig_info.MInfo()
    if variable.valueReference:
        info.id.value = variable.valueReference

    if variable:
        info.value = variable

    if variable.type:
        info.type.value = variable.type

    if variable.quantity:
        info.unit.value = variable.quantity

    return info

<DTIG_METHOD(PUBLIC)>
def direction_to_freecad(direction):
    match = re.search(fr'(-)?(\w)', direction)
    if not match:
        return None, None

    return match.groups()[0] != None, self.app.getObject(f'{match.groups()[1].capitalize()}_Axis')

<DTIG_METHOD(PUBLIC)>
def get_object(label):
    obj_list = self.app.getObjectsByLabel(label)
    if len(obj_list) > 0:
        return obj_list[0]

    return None

<DTIG_CALLBACK(RUNMODEL)>
def run_model() -> None:
    with self.condition:
        self.condition.wait_for(lambda: self.state == dtig_state.INITIALIZED or self.state == dtig_state.STOPPED)
        if self.state == dtig_state.STOPPED:
            return

    print(f'Initializing FreeCAD FEM model')

    # Simulation loop
    import Mesh
    from femtools import ccxtools
    from femmesh.femmesh2mesh import femmesh_2_mesh

    print("Waiting for start")
    while self.state != dtig_state.STOPPED:
        with self.condition:
            self.condition.wait_for(lambda: self.state == dtig_state.RUNNING or self.state == dtig_state.STOPPED)
            if self.state == dtig_state.STOPPED:
                break

        print(f'Running with state: {self.state}')

        fea = ccxtools.FemToolsCcx(analysis=self.analysis_object, solver=self.solver)
        fea.purge_results()
        if not fea.run():
            print("Simulation failed")
        else:
            for obj in self.analysis_object.Group:
                if obj.isDerivedFrom('Fem::FemResultObject'):
                    out_mesh = femmesh_2_mesh(self.mesh_object.FemMesh, obj)
                    Mesh.Mesh(out_mesh).write('Results.obj')
                    self.results = obj
                    break

        # Save document with results
        self.app.save()

        with self.condition:
            if self.state != dtig_state.STOPPED:
                self.state = dtig_state.IDLE

        print(f'FreeCAD FEM simulation done')

<DTIG_CALLBACK(SET_INPUT)>
def set_inputs(reference, any_value):
    DTIG_IF(NOT DTIG_INPUTS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no inputs")
    DTIG_ELSE

    DTIG_FOR(DTIG_INPUTS)

    DTIG_IF(DTIG_INDEX == 0)
    if reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_ELSE
    elif reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_END_IF

        value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
        if not any_value.Unpack(value):
            return self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {reference}")

        DTIG_IF(DTIG_ITEM_TYPE == TYPE_FORCE)

        if not value.object:
            return self.return_code(dtig_code.FAILURE, f"No object provided: {reference}")

        # If force already exists, use that
        constraint = self.get_object(reference)
        if not constraint:
            constraint = DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)(self.app, reference)

        obj_ref = self.app.getObject(value.object.value)
        if not obj_ref:
            return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")

        if value.reference:
            constraint.References = [(obj_ref, value.reference.value)]
        if value.direction:
            reverse, direction = self.direction_to_freecad(value.direction.value)
            constraint.Direction = (direction, [""])
            constraint.Reversed = reverse
        if value.value:
            constraint.Force = value.value.value

        self.analysis_object.addObject(constraint)

        DTIG_END_IF

        self.app.recompute()
        self.app.save()

        return self.return_code(dtig_code.SUCCESS)

    DTIG_END_FOR
    DTIG_END_IF

<DTIG_CALLBACK(GET_OUTPUT)>
def get_output_callback(references):
    DTIG_IF(NOT DTIG_OUTPUTS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no outputs")
    DTIG_ELSE

    # Check whether results are available, for FreeCAD, the outputs are only available once the model finished running
    if not self.results:
        return self.return_code(dtig_code.FAILURE, "No output available")

    return_message = self.return_code(dtig_code.SUCCESS)
    for reference in references:
    DTIG_FOR(DTIG_OUTPUTS)

        DTIG_IF(DTIG_INDEX == 0)
        if reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF

            any_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)

            DTIG_IF(DTIG_ITEM_TYPE == TYPE_MESH)
            import Mesh
            from femmesh.femmesh2mesh import femmesh_2_mesh

            out_mesh = femmesh_2_mesh(self.mesh_object.FemMesh, self.results)
            Mesh.Mesh(out_mesh).write(DTIG_STR(DTIG_ITEM_DEFAULT))
            any_value.value = DTIG_STR(DTIG_ITEM_DEFAULT)

            DTIG_ELSE

            property_value = self.results.getPropertyByName(reference)
            if not property_value:
                return self.return_code(dtig_code.FAILURE, f'No property: {reference}')

            DTIG_IF(KEY_MODIFIER == DTIG_ITEM)
            any_value.value = DTIG_ITEM_MODIFIER(property_value)
            DTIG_ELSE
            any_value.value = property_value
            DTIG_END_IF

            DTIG_END_IF

            any_msg = any_pb2.Any()
            any_msg.Pack(any_value)
            return_message.values.identifiers.append(reference)
            return_message.values.values.append(any_msg)

            return return_message
    DTIG_END_IF
    DTIG_END_FOR

<DTIG_CALLBACK(SET_PARAMETER)>
def set_parameters(reference, any_value):
    DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no inputs")
    DTIG_ELSE

    DTIG_FOR(DTIG_PARAMETERS)

    DTIG_IF(DTIG_INDEX == 0)
    if reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_ELSE
    elif reference == DTIG_STR(DTIG_ITEM_NAME):
    DTIG_END_IF

        value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
        if not any_value.Unpack(value):
            return self.return_code(dtig_code.FAILURE, f"Failed to unpack value: {reference}")

        # If object already exists, use that
        parameter = self.get_object(reference)
        if not parameter:
            parameter = DTIG_TYPE_TO_FUNCTION(DTIG_ITEM_TYPE)(self.app, reference)

        DTIG_IF(DTIG_ITEM_TYPE == TYPE_FORCE)

        if not value.object:
            return self.return_code(dtig_code.FAILURE, f"No object provided: {reference}")

        obj_ref = self.app.getObject(value.object.value)
        if not obj_ref:
            return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")

        if value.reference:
            parameter.References = [(obj_ref, value.reference.value)]
        if value.direction:
            reverse, direction = self.direction_to_freecad(value.direction.value)
            parameter.Direction = (direction, [""])
            parameter.Reversed = reverse
        if value.value:
            parameter.Force = value.value.value

        DTIG_ELSE_IF(DTIG_ITEM_TYPE == TYPE_MATERIAL)

        # Update material
        mat = parameter.Material
        mat['Name'] = value.name
        mat['YoungsModulus'] = value.youngs_modulus
        mat['PoissonRatio'] = value.poisson_ratio
        mat['Density'] = value.density
        parameter.Material = mat

        DTIG_ELSE_IF(DTIG_ITEM_TYPE == TYPE_FIXTURE)

        if not value.object:
            return self.return_code(dtig_code.FAILURE, f"No object provided: {reference}")

        if not value.reference:
            return self.return_code(dtig_code.FAILURE, f"No reference provided: {reference}")

        obj_ref = self.app.getObject(value.object.value)
        if not obj_ref:
            return self.return_code(dtig_code.UNKNOWN_OPTION, f"Unknown output: {reference}")

        parameter.References = [(obj_ref, value.reference.value)]

        DTIG_END_IF

        self.analysis_object.addObject(parameter)

        self.app.recompute()
        self.app.save()
        return self.return_code(dtig_code.SUCCESS)
    DTIG_END_FOR
    DTIG_END_IF

<DTIG_CALLBACK(GET_PARAMETER)>
def get_parameter(references):
    DTIG_IF(NOT DTIG_PARAMETERS_LENGTH)
    return self.return_code(dtig_code.FAILURE, "Model has no parameters")
    DTIG_ELSE

    return_message = self.return_code(dtig_code.SUCCESS)
    for reference in references:
    DTIG_FOR(DTIG_PARAMETERS)
        DTIG_IF(DTIG_INDEX == 0)
        if reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_ELSE
        elif reference == DTIG_STR(DTIG_ITEM_NAME):
        DTIG_END_IF
            any_value = DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE)
            property_value = self.get_object(reference)
            if not property_value:
                return self.return_code(dtig_code.FAILURE, f'No property: {reference}')
            DTIG_IF(DTIG_ITEM_TYPE == TYPE_MATERIAL)

            any_value.name = property_value.Material['Name']
            any_value.youngs_modulus = property_value.Material['YoungsModulus']
            any_value.poisson_ratio = property_value.Material['PoissonRatio']
            any_value.density = property_value.Material['Density']

            DTIG_ELSE_IF(DTIG_ITEM_TYPE == TYPE_FIXTURE)

            any_value.object.value    = property_value.References[0][0].Label
            any_value.reference.value = ", ".join(map(str, property_value.References[0][1]))

            DTIG_ELSE

            any_value.value = property_value

            DTIG_END_IF

            any_msg = any_pb2.Any()
            any_msg.Pack(any_value)
            return_message.values.identifiers.append(reference)
            return_message.values.values.append(any_msg)

            return return_message
    DTIG_END_IF
    DTIG_END_FOR
