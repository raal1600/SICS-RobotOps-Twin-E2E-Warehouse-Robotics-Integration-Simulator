"""Fixed Blender entry point: reset/query/capture/pick only, JSON data, no eval/exec."""

import copy
import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import bpy
from mathutils import Vector


def cube(name, location, scale, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    material = bpy.data.materials.new(name + "Material")
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("SoftEdges", "BEVEL")
    bevel.width = 0.03
    bevel.segments = 2
    return obj


def camera(name, location, target):
    bpy.ops.object.camera_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    obj.data.type = "ORTHO"
    obj.data.ortho_scale = 3.8
    return obj


def scene(world):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    collection = bpy.data.collections.new("RobotOpsTwin")
    bpy.context.scene.collection.children.link(collection)
    cube("RobotOpsTwin/Cell", (0, 0, -0.05), (2.7, 1.8, 0.1), (0.12, 0.18, 0.23))
    cube("Robot", (0, 0.6, 0.4), (0.18, 0.18, 0.8), (0.18, 0.5, 0.62))
    cube("RobotArm", (0, 0.25, 0.85), (0.15, 0.8, 0.12), (0.3, 0.65, 0.72))
    gripper = cube("Gripper", (0, 0, 0.8), (0.15, 0.14, 0.14), (0.85, 0.65, 0.17))
    for i, loc in enumerate(world["locations"]):
        x, y, z = loc["pose"]["position"]
        name = "SourceTote" if i == 0 else "DestinationTote"
        tote = cube(name, (x, y, 0.04), (0.55, 0.65, 0.08), (0.2, 0.32, 0.38))
        tote["location_id"] = loc["location_id"]
        for dx, dy, sx, sy in [
            (-0.28, 0, 0.025, 0.65),
            (0.28, 0, 0.025, 0.65),
            (0, -0.33, 0.56, 0.025),
            (0, 0.33, 0.56, 0.025),
        ]:
            cube(name + f"Wall{dx}{dy}", (x + dx, y + dy, 0.11), (sx, sy, 0.15), (0.3, 0.45, 0.52))
    colors = [(0.76, 0.19, 0.15), (0.15, 0.38, 0.72), (0.22, 0.62, 0.3)]
    for i, item in enumerate(world["objects"]):
        ident = item["product"]["product_id"]
        obj = cube("Products/" + ident, item["pose"]["position"], (0.13, 0.13, 0.13), colors[i % 3])
        obj["product_id"] = ident
        obj["location_id"] = item["location_id"]
    overview = camera("OverviewCamera", (2.6, -3.6, 2.8), (0, 0, 0.25))
    camera("ObservationCamera", (0, 0, 3), (0, 0, 0))
    bpy.context.scene.camera = overview
    bpy.ops.object.light_add(type="AREA", location=(0, -1, 4))
    bpy.context.object.data.energy = 500
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 4
    bpy.context.scene.world.color = (0.12, 0.12, 0.12)
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "CPU"
    bpy.context.scene.cycles.samples = 16
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 560
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.frame_end = 100
    return gripper


def record_motion(directory, command, pacing=0):
    """Export evaluated Blender poses, including partial recordings after interruption."""
    objects = sorted((obj for obj in bpy.data.objects if obj.type == "MESH"), key=lambda o: o.name)
    bpy.context.scene.frame_set(1)
    recording = {
        "schema_version": "1.0",
        "source": "BLENDER_EVALUATED_SCENE",
        "command_id": command["command_id"],
        "job_id": command["job_id"],
        "scene_epoch": command["scene_epoch"],
        "product_id": command["product_id"],
        "frame_id": command["target_pose"]["frame_id"],
        "unit": "m",
        "fps": 24,
        "total_frames": 100,
        "complete": False,
        "objects": [
            {
                "name": obj.name,
                "position": list(obj.matrix_world.translation),
                "size": list(obj.dimensions),
                "color": list(obj.data.materials[0].diffuse_color[:3]),
                "product_id": obj.get("product_id"),
                "location_id": obj.get("location_id"),
            }
            for obj in objects
        ],
        "frames": [],
    }
    start = time.monotonic()
    for frame in range(1, 101):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        phase = next(
            label
            for end, label in [
                (19, "APPROACH"),
                (20, "ATTACH"),
                (40, "LIFT"),
                (70, "TRANSFER"),
                (90, "DETACH"),
                (100, "RETRACT"),
            ]
            if frame <= end
        )
        recording["frames"].append(
            {
                "frame": frame,
                "phase": phase,
                "positions": {
                    obj.name: list(obj.matrix_world.translation)
                    for obj in objects
                    if obj.animation_data
                },
            }
        )
        recording["complete"] = frame == 100
        if frame == 1 or frame % 4 == 0:
            temporary = directory / "motion.tmp"
            temporary.write_text(json.dumps(recording), encoding="utf-8")
            temporary.replace(directory / "motion.json")
        if pacing:
            time.sleep(max(0, start + frame * pacing - time.monotonic()))


def main():
    directory = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    if (
        set(request) - {"schema_version", "operation", "world", "command", "visual_frame_seconds"}
        or request["schema_version"] != "1.0"
    ):
        raise ValueError("INVALID_RUNTIME_ENVELOPE")
    operation = request["operation"]
    if operation not in {"reset", "query", "capture", "pick"}:
        raise ValueError("UNSUPPORTED_OPERATION")
    world = copy.deepcopy(request["world"])
    command = request["command"]
    if "--record-existing" in sys.argv:
        response = json.loads((directory / "response.json").read_text(encoding="utf-8"))
        if (
            operation != "pick"
            or response["command_id"] != command["command_id"]
            or response["scene_sha256"]
            != hashlib.sha256((directory / "scene.blend").read_bytes()).hexdigest()
        ):
            raise ValueError("INVALID_SAVED_SCENE")
        bpy.ops.wm.open_mainfile(filepath=str(directory / "scene.blend"), use_scripts=False)
        record_motion(directory, command)
        return
    pacing = request.get("visual_frame_seconds", 0)
    if not isinstance(pacing, (float, int)) or not math.isfinite(pacing) or not 0 <= pacing <= 0.1:
        raise ValueError("INVALID_VISUAL_PACING")
    steps = []
    gripper = scene(world)
    if operation == "pick":
        if command["kind"] != "PICK_AND_PLACE" or command["scene_epoch"] != world["scene_epoch"]:
            raise ValueError("INVALID_COMMAND")
        obj = bpy.data.objects["Products/" + command["product_id"]]
        if obj["location_id"] != command["source_id"]:
            raise ValueError("SOURCE_PRECONDITION_FAILED")
        source = obj.location.copy()
        target = Vector(command["target_pose"]["position"])
        if not all(math.isfinite(v) for v in target):
            raise ValueError("INVALID_POSE")
        obj.keyframe_insert(data_path="location", frame=1)
        for frame, position, label in [
            (10, source + Vector((0, 0, 0.35)), "APPROACH"),
            (20, source, "ATTACH"),
            (40, source + Vector((0, 0, 0.4)), "LIFT"),
            (70, target + Vector((0, 0, 0.4)), "TRANSFER"),
            (90, target, "DETACH"),
        ]:
            gripper.location = position
            gripper.keyframe_insert(data_path="location", frame=frame)
            if frame == 20:
                obj.parent = gripper
                obj.location = (0, 0, 0)
            if frame == 90:
                obj.parent = None
                obj.location = target
            steps.append(label)
        obj.animation_data_clear()
        for frame, position in [
            (1, source),
            (20, source),
            (40, source + Vector((0, 0, 0.4))),
            (70, target + Vector((0, 0, 0.4))),
            (90, target),
            (100, target),
        ]:
            obj.location = position
            obj.keyframe_insert(data_path="location", frame=frame)
        gripper.location = target + Vector((0, 0, 0.35))
        gripper.keyframe_insert(data_path="location", frame=100)
        obj["location_id"] = command["destination_id"]
        # Observe the actual keyed scene, not a separately invented browser trajectory.
        record_motion(directory, command, pacing)
        bpy.context.scene.frame_set(100)
        bpy.context.view_layer.update()
        for item in world["objects"]:
            actual = bpy.data.objects["Products/" + item["product"]["product_id"]]
            item["pose"]["position"] = list(actual.matrix_world.translation)
            item["location_id"] = actual["location_id"]
            item["attached"] = False
        world["step"] += 1
        world["timestamp"] = datetime.now(UTC).isoformat()
    bpy.context.scene.frame_set(100)
    bpy.ops.wm.save_as_mainfile(filepath=str(directory / "scene.blend"))
    bpy.context.scene.render.filepath = str(directory / "capture.png")
    bpy.ops.render.render(write_still=True)
    response = {
        "schema_version": "1.0",
        "world": world,
        "command_id": command["command_id"] if command else None,
        "effect_count": 1 if operation == "pick" else 0,
        "steps": steps,
        "blender_version": bpy.app.version_string,
        "scene_sha256": hashlib.sha256((directory / "scene.blend").read_bytes()).hexdigest(),
        "motion_sha256": hashlib.sha256((directory / "motion.json").read_bytes()).hexdigest()
        if operation == "pick"
        else None,
        "object_names": sorted(obj.name for obj in bpy.data.objects),
    }
    temporary = directory / "response.tmp"
    temporary.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    temporary.replace(directory / "response.json")


if __name__ == "__main__":
    main()
