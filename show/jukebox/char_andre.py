from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.prepScene import PrepSceneComponent
from src.components.fileImport import GuideFileImport
from src.components.fileImport import ModelFileImport
from src.components.control import ControlGenerator
from src.components.jointRenderer import JointRenderer
from src.components.spaceSwitch import SpaceSwitch
from src.components.matrixInverse import MatrixInverse
from src.components.matricesMult import MatricesMult
from src.assembly.biped_spine import BipedSpine
from src.assembly.biped_leg import BipedLeg
from src.assembly.biped_neck import BipedNeck
from src.assembly.biped_finger import BipedFinger

from src.components.skinClusterImport import SkinClusterImport
from src.rig.context import Context

from src.lib.naming import Name
from src.rig.controls import shape

from src.assembly import biped_arm

STAGES_BUILD_FULL = ("prepare", "connect", "load_guides", "load_build_data", "build", "cleanup", "import_deformer")

builder = Builder("CharAndre")
builder.context = Context("andre", r"P:\AndreJukeBox\assets", "character")

builder.modules.append(PrepSceneComponent(Name("prepScene")))

import_guides = GuideFileImport(Name("guides"))
import_guides.version = -1
builder.add_module(import_guides)

placer = ControlGenerator(Name("placer"))
placer.default_shape = shape.ShapeData(
    points=shape.scale(shape.CIRCLE, 45),
    color=shape.COLOR_YELLOW,
    degree=1)
builder.modules.append(placer)

import_model = ModelFileImport(Name("importModel"))
import_model.path = builder.context.asset_path() / "model" / "andre_model.ma"
import_model.version = -1
import_model.in_parent_mtx.connect(placer.out_normalized_mtx)
builder.modules.append(import_model)

skin_cluster_import = SkinClusterImport(Name("skinClusterImport"))
skin_cluster_import.meshes = import_model.meshes
builder.add_module(skin_cluster_import)

placer_inverse = MatrixInverse(placer.name.replace(extra="inverse"))
placer_inverse.in_mtx.connect(placer.out_world_mtx)
placer_inverse.external_structure = placer.structure
builder.add_module(placer_inverse)

root = ControlGenerator(Name("root", side="c"))
root.in_parent_mtx.connect(placer.out_normalized_mtx)
root.default_shape = shape.ShapeData(
    points=shape.scale(shape.CIRCLE, 25),
    color=shape.COLOR_YELLOW,
    degree=1)
builder.modules.append(root)

spine = BipedSpine(Name("spine", side="c"))
spine.in_localize.connect(placer_inverse.out_mtx)
spine.in_parent.connect(root.out_normalized_mtx)
builder.add_module(spine)

neck = BipedNeck(Name("neck", side="c"))
neck.in_parent.connect(spine.out_end)
# neck spsw
neck.in_localize.connect(placer_inverse.out_mtx)
neck.neck_spsw.target_mtxs.connect(spine.out_end, dst_index=0)
neck.neck_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=1)
neck.neck_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=2)
neck.neck_spsw_attr.settings["en"] = "spine:root:global"
# head spsw
neck.head_spsw.target_mtxs.connect(neck.neck_ctrl.out_normalized_mtx, dst_index=0)
neck.head_spsw.target_mtxs.connect(spine.out_end, dst_index=1)
neck.head_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=2)
neck.head_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=3)
neck.head_spsw_attr.settings["en"] = "neck:spine:root:global"
builder.add_module(neck)

for side in "lr":
    clavicle = ControlGenerator(Name("clavicle", side=side))
    clavicle.in_parent_mtx.connect(spine.out_end)
    clavicle.default_shape = shape.ShapeData(
        points=shape.translate(shape.rotate(shape.scale(shape.QUATER_SPHERE, 12), [90, 90, 0]), [5, 0, 0]),
        color=shape.SIDE_COLOR[side],
        degree=1)
    builder.modules.append(clavicle)

    clavicle_local = MatricesMult(clavicle.name.replace(extra="local"))
    clavicle_local.external_structure = clavicle.structure
    clavicle_local.in_mtxs.connect(clavicle.out_normalized_mtx, dst_index=0)
    clavicle_local.in_parent_mtx.connect(placer_inverse.out_mtx)
    builder.add_module(clavicle_local)

    clavicle_output = JointRenderer(clavicle.name.replace(extra="skin"))
    clavicle_output.external_structure = clavicle.structure
    clavicle_output.in_mtxs.connect(clavicle_local.out_mtxs)
    clavicle_output.nice_name = clavicle.name
    clavicle_output.for_skinning = True
    builder.add_module(clavicle_output)

    arm = biped_arm.BipedArm(Name("arm", side=side))
    arm.in_global.connect(placer.out_normalized_mtx)
    arm.in_parent.connect(clavicle.out_normalized_mtx)
    arm.in_localize.connect(placer_inverse.out_mtx)
    arm.in_local_parent.connect(clavicle_local.out_mtxs, src_index=0)
    arm.pole_offset.distance = 50
    arm.fk_ik_attr.settings["dv"] = 0
    # arm fk spsw
    arm.fk_spsw.target_mtxs.connect(clavicle.out_normalized_mtx, dst_index=0)
    arm.fk_spsw.target_mtxs.connect(spine.out_end, dst_index=1)
    arm.fk_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=2)
    arm.fk_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=3)
    arm.fk_spsw_attr.settings["en"] = "clavicle:spine:root:global"
    arm.fk_spsw_attr.settings["dv"] = 1
    # arm ik spsw
    arm.ik_spsw.target_mtxs.connect(clavicle.out_normalized_mtx, dst_index=0)
    arm.ik_spsw.target_mtxs.connect(spine.out_end, dst_index=1)
    arm.ik_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=2)
    arm.ik_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=3)
    arm.ik_spsw_attr.settings["en"] = "clavicle:spine:root:global"
    arm.ik_spsw_attr.settings["dv"] = 3
    # arm pole spsw
    arm.pole_spsw.target_mtxs.connect(arm.ik_handle.out_normalized_mtx, dst_index=0)
    arm.pole_spsw.target_mtxs.connect(clavicle.out_normalized_mtx, dst_index=1)
    arm.pole_spsw.target_mtxs.connect(spine.out_end, dst_index=2)
    arm.pole_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=3)
    arm.pole_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=4)
    arm.pole_spsw_attr.settings["en"] = "hand:clavicle:spine:root:global"
    arm.pole_spsw_attr.settings["dv"] = 4
    builder.modules.append(arm)

    arm.switch.add_seperator("Finger")

    for finger in ["thumb", "index", "middle", "ring", "pinky"]:
        finger_fk_ik = arm.switch.add_attr(f"{finger}_fkIk", at="short", min=0, max=1, k=True)

        finger_mod = BipedFinger(
            name=Name(finger, side=side),
            has_metacarpal=finger is not "thumb")
        finger_mod.in_parent.connect(arm.out_joints, src_index=2)
        finger_mod.in_localize.connect(placer_inverse.out_mtx)
        finger_mod.fk_ik_attr.connect(finger_fk_ik)
        builder.add_module(finger_mod)

for side in "lr":
    leg = BipedLeg(Name("leg", side=side))
    leg.in_global.connect(placer.out_normalized_mtx)
    leg.in_parent.connect(spine.out_start)
    leg.in_localize.connect(placer_inverse.out_mtx)
    leg.in_local_parent.connect(spine.out_local_start)
    leg.ball_roll_compensate.settings["dv"] = 10
    leg.pole_offset.distance = 50
    leg.fk_ik_attr.settings["dv"] = 1
    # arm fk spsw
    leg.fk_spsw.target_mtxs.connect(spine.out_start, dst_index=0)
    leg.fk_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=1)
    leg.fk_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=2)
    leg.fk_spsw_attr.settings["en"] = "hip:root:global"
    leg.fk_spsw_attr.settings["dv"] = 1
    # arm ik spsw
    leg.ik_spsw.target_mtxs.connect(spine.out_start, dst_index=0)
    leg.ik_spsw.target_mtxs.connect(root.out_normalized_mtx, dst_index=1)
    leg.ik_spsw.target_mtxs.connect(placer.out_normalized_mtx, dst_index=2)
    leg.ik_spsw_attr.settings["en"] = "hip:root:global"
    leg.ik_spsw_attr.settings["dv"] = 2
    builder.add_module(leg)


def run(stages: tuple[str] = STAGES_BUILD_FULL):
    builder.stages = stages
    # builder.parallel_stages = ["load_guide_data", "load_build_data", "load_deformer_data"]

    monitor = Monitor(builder)
    builder.run()
