"""Fixed, data-only renderer for already committed ideal-gantry controller samples.

No calibration/kinematics solver, sensor measurement generation or physical effect
runs inside Blender. Python sensor images remain the authoritative capture artifacts.
Base coordinates are z-up. Cameras here are presentation views, not synthetic optics.
"""

import copy
import hashlib
import json
import math

import bpy
from mathutils import Vector

from blender.scripts.hkm_scene import bake_frame, build_scene, sampled_primitives


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("NONFINITE_PRESENTATION_DATA")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    if isinstance(value, list):
        for item in value:
            _finite(item)


def _primitives(scene):
    result = copy.deepcopy(scene["objects"])
    for item in result:
        item["semantic_tags"] = [*(item.get("semantic_tags") or []), "dynamic"]
        item["material_role"] = item.get("material_role") or "measured-cell"
        item["parent_name"] = None
        # Optional contract identifiers are absent, not Blender IDProperty None.
        for key in ("product_id", "location_id", "tool_id"):
            if item.get(key) is None:
                item.pop(key, None)
    return result


def _sample_recording(original):
    recording = copy.deepcopy(original)
    recording["source"] = "BLENDER_EVALUATED_CONTROLLER_REPLAY"
    for frame in recording["frames"]:
        bpy.context.scene.frame_set(frame["frame"])
        samples = sampled_primitives()
        frame["positions"] = {obj["name"]: obj["position"] for obj in samples}
        frame["transforms"] = {
            obj["name"]: {
                "schema_version": "2.0",
                **{key: obj[key] for key in ("position", "quaternion_xyzw", "scale", "visible")},
            }
            for obj in samples
        }
    return recording


def _frame_overview(camera):
    """Display framing only: include both physical sensor housings and the cell."""
    bpy.context.view_layer.update()
    local = [
        camera.matrix_world.inverted() @ (obj.matrix_world @ Vector(corner))
        for obj in bpy.data.objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    low = [min(point[index] for point in local) for index in (0, 1)]
    high = [max(point[index] for point in local) for index in (0, 1)]
    center = Vector(((low[0] + high[0]) / 2, (low[1] + high[1]) / 2, 0))
    camera.location += camera.matrix_world.to_quaternion() @ center
    camera.data.ortho_scale = 1.14 * max(high[0] - low[0], (high[1] - low[1]) * 960 / 640)


def run(directory, record_existing=False):
    raw = (directory / "request.json").read_bytes()
    if len(raw) > 32_000_000:
        raise ValueError("PRESENTATION_REQUEST_TOO_LARGE")
    request = json.loads(raw)
    _finite(request)
    if (
        set(request) != {"schema_version", "operation", "scene", "recording"}
        or request["schema_version"] != "3.0"
    ):
        raise ValueError("INVALID_MEASURED_PRESENTATION_ENVELOPE")
    if request["operation"] not in {"present_current_scene", "present_committed_controller"}:
        raise ValueError("UNSUPPORTED_PRESENTATION_OPERATION")
    original = request["recording"]
    scene = request["scene"]
    if (
        not 1 <= len(scene["objects"]) <= 512
        or scene.get("robot_profile_version") != "synthetic_calibration_gantry_v1"
    ):
        raise ValueError("MEASURED_PRESENTATION_PROFILE_REQUIRED")
    if original is not None and (
        not original["complete"]
        or not 1 <= len(original["frames"]) <= 720
        or original["source"] != "SYNTHETIC_CONTROLLER_REPORTS"
        or original["schema_version"] != "3.0"
    ):
        raise ValueError("COMMITTED_CONTROLLER_RECORDING_REQUIRED")
    if record_existing:
        response = json.loads((directory / "response.json").read_text(encoding="utf-8"))
        for name in ("request.json", "scene.blend"):
            if (
                hashlib.sha256((directory / name).read_bytes()).hexdigest()
                != response["hashes"][name]
            ):
                raise ValueError("SAVED_PRESENTATION_HASH_MISMATCH")
        bpy.ops.wm.open_mainfile(filepath=str(directory / "scene.blend"), use_scripts=False)
    else:
        primitives = _primitives(scene)
        overview = build_scene(
            primitives, [camera for camera in scene["cameras"] if camera["role"] == "PRESENTATION"]
        )
        overview.data.ortho_scale = 2.5
        bpy.context.scene.render.fps = 24
        bpy.context.scene.frame_end = original["total_frames"] if original else 1
        if original:
            for frame in original["frames"]:
                sample = copy.deepcopy(primitives)
                for obj in sample:
                    transform = frame["transforms"].get(obj["name"])
                    if transform:
                        obj.update(
                            {
                                key: transform[key]
                                for key in ("position", "quaternion_xyzw", "scale", "visible")
                            }
                        )
                bake_frame(frame["frame"], sample)
        bpy.ops.object.light_add(type="AREA", location=(0, -1, 3))
        bpy.context.object.data.energy = 350
        bpy.context.object.data.size = 3
        bpy.context.scene.world.color = (0.16, 0.16, 0.16)
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.device = "CPU"
        bpy.context.scene.cycles.samples = 8
        bpy.context.scene.render.resolution_x = 960
        bpy.context.scene.render.resolution_y = 640
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.context.scene.frame_set(original["total_frames"] if original else 1)
        _frame_overview(overview)
        bpy.ops.wm.save_as_mainfile(filepath=str(directory / "scene.blend"))
        bpy.context.scene.render.filepath = str(directory / "capture.png")
        bpy.ops.render.render(write_still=True)
    if original:
        (directory / "motion.json").write_text(
            json.dumps(_sample_recording(original), allow_nan=False), encoding="utf-8"
        )
    names = ["request.json", "scene.blend", "capture.png", *(["motion.json"] if original else [])]
    response = {
        "schema_version": "3.0",
        "authority": "PRESENTATION_ONLY_NO_EXECUTION",
        "source": "Committed Python controller samples"
        if original
        else "Current physical simulator scene",
        "command_id": original["command_id"] if original else None,
        "hashes": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names
        },
        "object_names": sorted(bpy.data.objects.keys()),
        "sensor_rendering": "Separate Python RGB-D artifacts; Blender is presentation only",
    }
    # Kept compatible with the common read-only recording integrity check.
    response["motion_sha256"] = response["hashes"].get("motion.json")
    (directory / "response.json").write_text(json.dumps(response), encoding="utf-8")
