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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from robotops.presentation_io import write_snapshot  # noqa: E402
from robotops.scene_geometry import cell_meshes  # noqa: E402


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
    for mesh in cell_meshes(world):
        obj = cube(mesh["name"], mesh["position"], mesh["size"], mesh["color"])
        for label in ("product_id", "location_id"):
            if label in mesh:
                obj[label] = mesh[label]
    gripper = bpy.data.objects["Gripper"]
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
            write_snapshot(directory / "motion.json", recording)
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

        def machine_key(frame, position):
            x, y, z = position
            poses = {
                "Gripper": (x, y, z),
                "GripperLeft": (x - 0.095, y, z - 0.06),
                "GripperRight": (x + 0.095, y, z - 0.06),
                "RobotSpindle": (x, y, z + 0.525),
                "RobotCarriage": (x, 0.5, 1.3),
                "RobotArm": (x, y + 0.2, 1.18),
            }
            for name, pose in poses.items():
                part = bpy.data.objects[name]
                part.location = pose
                part.keyframe_insert(data_path="location", frame=frame)

        home = gripper.location.copy()
        product_keys = [
            (1, source),
            (20, source),
            (40, source + Vector((0, 0, 0.4))),
            (70, target + Vector((0, 0, 0.4))),
            (90, target),
            (100, target),
        ]
        machine_keys = [
            (1, home),
            (10, source + Vector((0, 0, 0.46))),
            (20, source + Vector((0, 0, 0.11))),
            (40, source + Vector((0, 0, 0.51))),
            (70, target + Vector((0, 0, 0.51))),
            (90, target + Vector((0, 0, 0.11))),
            (100, home),
        ]

        def interpolate(keys, frame):
            for (start, a), (end, b) in zip(keys, keys[1:], strict=False):
                if start <= frame <= end:
                    return a.lerp(b, (frame - start) / (end - start))
            raise ValueError("FRAME_OUTSIDE_TRAJECTORY")

        # Bake every sampled pose. Independent Bezier handles could otherwise
        # make a product slip relative to its gripper between phase boundaries.
        for frame in range(1, 101):
            obj.location = interpolate(product_keys, frame)
            obj.keyframe_insert(data_path="location", frame=frame)
            machine_key(frame, interpolate(machine_keys, frame))
        steps = ["APPROACH", "ATTACH", "LIFT", "TRANSFER", "DETACH"]
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
