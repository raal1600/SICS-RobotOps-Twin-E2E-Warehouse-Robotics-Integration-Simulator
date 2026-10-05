"""Bounded Blender authoring for the checked-in shared primitive representation.

No user code, asset downloads or natural-language execution. All object identity,
geometry and transforms come from our procedural scene and validated trajectory.
"""

import json
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

from robotops.hkm_geometry import camera_quaternion


def _matrix(primitive):
    x, y, z, w = primitive["quaternion_xyzw"]
    return Matrix.LocRotScale(
        Vector(primitive["position"]), Quaternion((w, x, y, z)), Vector(primitive["scale"])
    )


def _material(primitive):
    rgba = (*primitive["color"], primitive["opacity"])
    name = "Materials/" + primitive["material_role"] + "/" + str(rgba)
    material = bpy.data.materials.get(name)
    if material:
        return material
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Alpha"].default_value = primitive["opacity"]
    shader.inputs["Roughness"].default_value = (
        0.72 if primitive["material_role"] in {"carton", "rubber", "pouch", "floor"} else 0.38
    )
    shader.inputs["Metallic"].default_value = (
        0.55 if primitive["material_role"] == "metal" else 0.08
    )
    return material


def _mesh(primitive):
    if primitive["primitive"] == "box":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif primitive["primitive"] == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.5, depth=1)
    else:
        raise ValueError("UNSUPPORTED_PRIMITIVE")
    obj = bpy.context.object
    obj.name = primitive["name"]
    # Bake local dimensions into the mesh. Semantic parents always have unit
    # scale; their rectangular dimensions must not shear child transforms.
    for vertex in obj.data.vertices:
        for axis, size in enumerate(primitive["size"]):
            vertex.co[axis] *= size
    obj.data.update()
    obj.data.materials.append(_material(primitive))
    bevel = obj.modifiers.new("ProceduralEdgeSoftening", "BEVEL")
    bevel.width = min(min(primitive["size"]) * 0.12, 0.012)
    if primitive["material_role"] == "pouch":
        bevel.width = min(primitive["size"]) * 0.43
    bevel.segments = 3
    obj.rotation_mode = "QUATERNION"
    obj["primitive_definition"] = json.dumps(primitive, sort_keys=True)
    obj["primitive_size"] = primitive["size"]
    for key in ("product_id", "location_id", "tool_id"):
        if key in primitive:
            obj[key] = primitive[key]
    return obj


def _label(obj, primitive):
    text = primitive.get("label")
    if not text:
        return
    curve = bpy.data.curves.new(primitive["name"] + "/LabelFont", "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = min(0.095, max(0.018, primitive["size"][0] / max(2, len(text)) * 0.65))
    curve.extrude = 0.0005
    label = bpy.data.objects.new(primitive["name"] + "/Label", curve)
    bpy.context.scene.collection.objects.link(label)
    label.parent = obj
    label.location = (0, -primitive["size"][1] / 2 - 0.014, 0.055)
    label.rotation_euler = (math.pi / 2, 0, 0)
    material = bpy.data.materials.get("Materials/LabelText")
    if not material:
        material = bpy.data.materials.new("Materials/LabelText")
        material.diffuse_color = (0.91, 0.94, 0.97, 1)
    label.data.materials.append(material)


def build_scene(primitives, cameras):
    """Create procedural meshes and actual presentation/sensor cameras."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    names = {primitive["name"] for primitive in primitives}
    if len(names) != len(primitives) or len(names) > 512:
        raise ValueError("INVALID_PRIMITIVE_IDENTITIES")
    for primitive in primitives:
        _mesh(primitive)
    for primitive in primitives:
        obj = bpy.data.objects[primitive["name"]]
        parent = primitive["parent_name"]
        if parent is not None:
            if parent not in names:
                raise ValueError("MISSING_SEMANTIC_PARENT")
            obj.parent = bpy.data.objects[parent]
    # Assign parent poses first. Every primitive is a world-space definition.
    ordered = _parent_order(primitives)
    for primitive in ordered:
        obj = bpy.data.objects[primitive["name"]]
        obj.matrix_world = _matrix(primitive)
        obj.hide_render = not primitive["visible"]
        obj.hide_viewport = not primitive["visible"]
        bpy.context.view_layer.update()
        _label(obj, primitive)
    overview = None
    for spec in cameras:
        bpy.ops.object.camera_add(location=spec["position"])
        camera = bpy.context.object
        camera.name = spec["name"]
        x, y, z, w = camera_quaternion(spec["position"], spec["target"])
        camera.rotation_mode = "QUATERNION"
        camera.rotation_quaternion = (w, x, y, z)
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = 6.4 if spec["role"] == "PRESENTATION" else 4.3
        camera.data.clip_start = 0.02
        camera.data.clip_end = 30
        for key in ("sensor_id", "frame_id", "calibration_version", "camera_model_version", "role"):
            camera[key] = spec[key]
        if spec["role"] == "PRESENTATION":
            overview = camera
    if overview is None:
        raise ValueError("OVERVIEW_CAMERA_REQUIRED")
    bpy.context.scene.camera = overview
    return overview


def _parent_order(primitives):
    by_name = {item["name"]: item for item in primitives}
    result, added, active = [], set(), set()

    def visit(name):
        if name in added:
            return
        if name in active:
            raise ValueError("CYCLIC_SEMANTIC_PARENT")
        active.add(name)
        parent = by_name[name]["parent_name"]
        if parent in by_name:
            visit(parent)
        active.remove(name)
        added.add(name)
        result.append(by_name[name])

    for name in by_name:
        visit(name)
    return result


def bake_frame(frame_index, primitives):
    """Bake actual world poses under FIXED parents; never reparent mid-animation.

    Changing Blender parent ownership cannot be keyframed. Keeping the build-time
    parent and baking its inverse each frame preserves the world trajectory when
    a tool returns to its rack or a product attaches/releases. Recorded tool state
    conveys that semantic change independently from Blender object parenting.
    """
    bpy.context.scene.frame_set(frame_index)
    # Actual parent order is fixed at scene creation, even if semantic ownership
    # in the supplied sample changed during tool exchange.
    definitions = []
    for primitive in primitives:
        fixed = dict(primitive)
        obj = bpy.data.objects[primitive["name"]]
        fixed["parent_name"] = obj.parent.name if obj.parent else None
        definitions.append(fixed)
    matrices = {p["name"]: _matrix(p) for p in definitions}
    for primitive in _parent_order(definitions):
        if "dynamic" not in primitive["semantic_tags"]:
            continue
        obj = bpy.data.objects[primitive["name"]]
        desired = matrices[primitive["name"]]
        # Compute the local pose against the requested parent pose directly.
        # Updating the dependency graph after every link creates quadratic work
        # as the animation grows; one evaluation after the whole frame suffices.
        if obj.parent is not None:
            desired = (
                obj.matrix_parent_inverse.inverted()
                @ matrices[obj.parent.name].inverted()
                @ desired
            )
        obj.matrix_basis = desired
        # Visibility changes rebuild Blender's dependency graph. Reassigning an
        # unchanged flag does the same work for every mesh on every frame.
        # Keep the full animation, but only invalidate visibility when it changes.
        hidden = not primitive["visible"]
        if obj.hide_render != hidden:
            obj.hide_render = hidden
        if obj.hide_viewport != hidden:
            obj.hide_viewport = hidden
    bpy.context.view_layer.update()
    dynamic = [p for p in definitions if "dynamic" in p["semantic_tags"]]
    # Blender matrices are float32. A fixed parent several links away can
    # accumulate micrometre translation roundoff when a previously mounted
    # tool rests in the rack. Correct the evaluated residual in parent space;
    # this preserves the actual hierarchy and the recorded mesh dimensions.
    for _ in range(3):
        for primitive in dynamic:
            obj = bpy.data.objects[primitive["name"]]
            error = Vector(primitive["position"]) - obj.matrix_world.translation
            if obj.parent is not None:
                error = (
                    obj.parent.matrix_world @ obj.matrix_parent_inverse
                ).to_3x3().inverted() @ error
            obj.location += error
        bpy.context.view_layer.update()
    for primitive in dynamic:
        obj = bpy.data.objects[primitive["name"]]
        for path in ("location", "rotation_quaternion", "scale", "hide_render", "hide_viewport"):
            obj.keyframe_insert(data_path=path, frame=frame_index)


def sampled_primitives():
    """Export evaluated Blender transforms, preserving original local mesh sizes."""
    bpy.context.view_layer.update()
    result = []
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        definition = obj.get("primitive_definition")
        if definition is None:
            continue
        primitive = json.loads(definition)
        location, rotation, scale = obj.matrix_world.decompose()
        primitive["position"] = list(location)
        primitive["quaternion_xyzw"] = [rotation.x, rotation.y, rotation.z, rotation.w]
        primitive["scale"] = list(scale)
        primitive["visible"] = not obj.hide_render
        result.append(primitive)
    return result
