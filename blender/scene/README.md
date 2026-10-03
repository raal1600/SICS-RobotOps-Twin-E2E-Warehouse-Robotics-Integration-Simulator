# Synthetic scene source

`blender/scripts/runtime.py` reproducibly authors the scene in a fresh background
Blender process, using shared geometry from `robotops/scene_geometry.py`. Generated
.blend files and PNGs are runtime artifacts, not source
assets. Stable identities: RobotOpsTwin/Cell, Robot, RobotArm, Gripper, SourceTote,
DestinationTote, Products/<product_id>, OverviewCamera, ObservationCamera.

The robot is a stylized Cartesian gantry. Carriage, arm, spindle and gripper parts
carry the product at a fixed offset in every sampled attachment frame. The initial
3D app view shares this geometry; motion replay uses actual evaluated Blender poses.
It is not an HKM1800 model, validated
dynamics, a perception benchmark, or safety evidence. Product identity and actual
object coordinates are exported into a durable WorldState checkpoint, then pass
through ObservationModel before normal verification.
