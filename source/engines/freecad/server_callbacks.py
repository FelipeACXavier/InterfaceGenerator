# @callback(imports)
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

# @classname
FreeCADWrapper

# @callback(constructor)
# Engine specific members
self.stop_time  : float  = 10.0
self.step_size  : float  = 1e-3

self.app = None

self.solver = None
self.results = None
self.box_object = None
self.mesh_object = None
self.analysis_object = None

# @callback(initialize)
def parse_initialize(message) -> Message:
    if not message.HasField("model_name"):
        return self.return_code(dtig_code.INVALID_OPTION, f'No model provided')

    try:
        self.app = FreeCAD.open(message.model_name.value)

        print(f'Running with file: {message.model_name.value}')

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

# @callback(start)
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

# @callback(stop)
def parse_stop(message) -> Message:
    print(f'Stopping with: {message.mode}')
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(advance)
def parse_advance(self, message) -> Message:
    if message.HasField("step_size"):
        self.step_size = message.step_size.step

    self.state = dtig_state.RUNNING
    return self.return_code(dtig_code.SUCCESS)

# @callback(model_info)
def parse_model_info() -> Message:
    return dtig_return.MReturnValue(code=dtig_code.SUCCESS)

# @callback(get_status)
def parse_get_status() -> Message:
    return_value = dtig_return.MReturnValue(code=dtig_code.SUCCESS)
    return_value.status.state = self.state
    return return_value

# @method(public)
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

# @method(public)
def direction_to_freecad(direction):
    match = re.search(fr'(-)?(\w)', direction)
    if not match:
        return None, None

    return match.groups()[0] != None, self.app.getObject(f'{match.groups()[1].capitalize()}_Axis')

# @method(public)
def get_object(label):
    obj_list = self.app.getObjectsByLabel(label)
    if len(obj_list) > 0:
        return obj_list[0]

    return None

# @callback(runmodel)
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
