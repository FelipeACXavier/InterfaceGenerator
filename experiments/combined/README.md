# FMI + Matlab + FreeCAD + HLA
This experiment integrates 3 engines and uses HLA to synchronize their operation.

### FMI
Calculates the current position of a ball bouncing
- Outputs:
  - h: The current ball height
  - v: The current ball velocity

- Parameters:
  - g: Gravity
  - e: Coefficient of restitution
  - h0: The initial ball height
  - v0: The initial ball velocity

### Matlab
Calculates the force created by this ball
- Inputs:
  - v: The ball velocity

- Outputs:
  - f: The current force created by the ball

- Parameters:
  - floor: Floor height
  - mass: Mass of the ball

### Freecad
Calculates the displacement of a beam due to the bouncing ball
- Inputs:
  - Force: The force of the ball

- Outputs:
  - Mesh: The displacement mesh due to the input force
  - vonMises: The maximum stress caused by the input force
  - DisplacementLengths: Maximum displacement caused by the input force

- Parameters:
  - Material: The material of the beam
  - Fixed: The beam fixture