PATH='/media/felaze/NotAnExternalDrive/Projects/squashfs-root/usr/'
FREECADPATH = PATH + 'lib/'
FREECADFEMPATH = PATH + 'Mod/Fem/'
FREECADPYSIDEPATH = PATH + 'Ext/'

import sys
sys.path.append(FREECADPATH)
sys.path.append(FREECADFEMPATH)
sys.path.append(FREECADPYSIDEPATH)

import FreeCAD, FreeCADGui, Part
from tools.file_system import current_dir, remove_file

print("Opening document")
filename = f'{current_dir()}/FemTest.FCStd'
doc = FreeCAD.open(filename)

box_object = None
femmesh_obj = None
solver_object = None
material_object = None
analysis_object = None
force_constraint = None
fixed_constraint = None

print("Inspecting objects")
objects = doc.Objects
for ob in objects:
    print(f'{ob.Name} - {ob.Label}')

    if "Box" in ob.Name or "Axis" in ob.Name or \
       "Plane" in ob.Name or "Origin" in ob.Name:
        box_object = ob
        # for prop in ob.PropertiesList:
        #     print(f'- {prop:<30} {ob.getPropertyByName(prop)}')
    elif "Main" in ob.Label:
        pass
    else:
        doc.removeObject(ob.Name)

# import to create objects
import ObjectsFem

# analysis
if not analysis_object:
    print("Adding new analysis")
    analysis_object = ObjectsFem.makeAnalysis(doc)

if not solver_object:
    print("Adding new solver")
    solver_object = ObjectsFem.makeSolverCalculixCcxTools(doc)
    solver_object.GeometricalNonlinearity = 'linear'
    solver_object.ThermoMechSteadyState = True
    solver_object.MatrixSolverType = 'default'
    solver_object.IterationsControlParameterTimeUse = False
    solver_object.TimeEnd = 3.0
    for prop in solver_object.PropertiesList:
        print(f'- {prop:<30} {solver_object.getPropertyByName(prop)}')

    analysis_object.addObject(solver_object)

# material
if not material_object:
    print("Adding new material")
    material_object = ObjectsFem.makeMaterialSolid(doc)
    mat = material_object.Material
    mat['Name'] = "Steel-Generic"
    mat['YoungsModulus'] = "210000 MPa"
    mat['PoissonRatio'] = "0.30"
    mat['Density'] = "7900 kg/m^3"
    material_object.Material = mat
    analysis_object.addObject(material_object)

# fixed_constraint
if not fixed_constraint:
    print("Adding fixed constraint")
    fixed_constraint = ObjectsFem.makeConstraintFixed(doc)
    ref = None
    for ob in doc.Objects:
        if ob.Name == "Box":
            ref = ob
            break

    if not ref:
        print(f'No object {"Box"} found')
        exit(1)

    fixed_constraint.References = [(ref, "Face1")]
    analysis_object.addObject(fixed_constraint)

# force_constraint
if not force_constraint:
    print("Adding force constraint")
    force_constraint = ObjectsFem.makeConstraintForce(doc)
    ref = None
    for ob in doc.Objects:
        if ob.Name == "Box":
            ref = ob
            break

    if not ref:
        print(f'No object {"Box"} found')
        exit(1)

    force_constraint.References = [(ob, "Face2")]
    force_constraint.Force = 9000000.0
    import re
    direction = "-z"
    match = re.search(fr'(-)?(\w)', direction)
    if not match:
        print("Invalid direction")
        exit(1)

    print(match.groups())

    force_constraint.Direction = (doc.Z_Axis,[""])
    force_constraint.Reversed = match.groups()[0] != None
    analysis_object.addObject(force_constraint)

doc.recompute()
doc.save()

if not femmesh_obj:
    print("Adding mesh object")
    # Mesh properties are created at this stage
    femmesh_obj = ObjectsFem.makeMeshGmsh(doc, "FEMMeshGmsh")
    femmesh_obj.Part = doc.Box

    # Here we just compute the mesh using the desired algorithm
    from femmesh.gmshtools import GmshTools as gt

    print("Computing mesh")
    gmsh_mesh = gt(femmesh_obj)
    error = gmsh_mesh.create_mesh()
    if error:
        print(f'GMESH error: {error}')
        exit(1)

    analysis_object.addObject(femmesh_obj)

doc.recompute()

print("Running simulation")
import PySide
print("Running PySide")

from femtools import ccxtools

print("Running FemToolsCcx")
fea = ccxtools.FemToolsCcx(analysis=analysis_object, solver=solver_object)
fea.purge_results()
if not fea.run():
    print("Simulation failed")
    exit(1)

result_object = None
for m in analysis_object.Group:
    print(f'Looking for: {m.Name} - {m.Label}')
    if m.isDerivedFrom('Fem::FemResultObject'):
        result_object = m
        break

import Mesh
from femmesh.femmesh2mesh import femmesh_2_mesh
if result_object:
    print("Getting properties")
    for prop in result_object.PropertiesList:
        print(f'- {prop:<30} {result_object.getPropertyByName(prop)}')

    out_mesh = femmesh_2_mesh(femmesh_obj.FemMesh, result_object)
    Mesh.Mesh(out_mesh).write(f'{current_dir()}/Results.obj')

print("Saving results")
doc.save()
