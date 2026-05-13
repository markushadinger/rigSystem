from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.prepScene import PrepSceneComponent
from src.components.importModel import ImportModelComponent
from src.components.fileImport import GuideFileImport
from src.components.control import ControlGenerator
from src.components.jointRenderer import JointRenderer
from src.components.matrixInverse import MatrixInverse
from src.components.matricesMult import MatricesMult
from src.assembly.biped_spine import BipedSpine
from src.assembly.biped_leg import BipedLeg
from src.rig.context import Context

from src.lib.naming import Name
from src.rig.controls import shape

from src.assembly import biped_arm

STAGES_BUILD_FULL = ("prepare", "connect", "load_guides", "load_build_data", "build", "cleanup")
STAGES_BUILD_GUIDE = ("prepare", "load_guides")

builder = Builder("CharAndre")
builder.context = Context("andre", r"P:\AndreJukeBox\assets", "character")

builder.modules.append(PrepSceneComponent(Name("prepScene")))

import_guides = GuideFileImport(Name("guides"))
import_guides.version = -1
builder.add_module(import_guides)

import_model = ImportModelComponent("importModel")
import_model.path = r"P:\AndreJukeBox\assets\character\andre\model\andre_model.ma"
# builder.modules.append(import_model)

placer = ControlGenerator(Name("placer"))
placer.default_shape = shape.ShapeData(shape.scale(shape.CIRCLE, 30), color=shape.COLOR_YELLOW, degree=1)
builder.modules.append(placer)

placer_inverse = MatrixInverse(placer.name.replace(extra="inverse"))
placer_inverse.in_mtx.connect(placer.out_world_mtx)
placer_inverse.external_structure = placer.structure
builder.add_module(placer_inverse)

root = ControlGenerator(Name("root", side="c"))
root.in_parent_mtx.connect(placer.out_normalized_mtx)
root.default_shape = shape.ShapeData(shape.scale(shape.CIRCLE, 20), color=shape.COLOR_YELLOW, degree=1)
builder.modules.append(root)

spine = BipedSpine(Name("spine", side="c"))
spine.in_localize.connect(placer_inverse.out_mtx)
spine.in_parent.connect(root.out_normalized_mtx)
builder.add_module(spine)


for side in "lr":
    clavicle = ControlGenerator(Name("clavicle", side=side))
    clavicle.in_parent_mtx.connect(spine.out_end)
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
    builder.modules.append(arm)

    leg = BipedLeg(Name("leg", side=side))
    leg.in_global.connect(placer.out_normalized_mtx)
    leg.in_parent.connect(spine.out_start)
    leg.in_localize.connect(placer_inverse.out_mtx)
    builder.add_module(leg)


def run(stages: tuple[str] = STAGES_BUILD_FULL):
    builder.stages = stages
    # builder.parallel_stages = ["load_guide_data", "load_build_data", "load_deformer_data"]

    monitor = Monitor(builder)
    builder.run()
