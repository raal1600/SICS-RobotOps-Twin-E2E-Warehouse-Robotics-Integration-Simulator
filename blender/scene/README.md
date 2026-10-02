# Synthetic scene source

`blender/scripts/runtime.py` reproducibly authors the scene in a fresh background
Blender process. Generated .blend files and PNGs are runtime artifacts, not source
assets. Stable identities: RobotOpsTwin/Cell, Robot, RobotArm, Gripper, SourceTote,
DestinationTote, Products/<product_id>, OverviewCamera, ObservationCamera.

The robot is generic simplified geometry. It is not an HKM1800 model, validated
dynamics, a perception benchmark, or safety evidence. Product identity and actual
object coordinates are exported into a durable WorldState checkpoint, then pass
through ObservationModel before normal verification.
