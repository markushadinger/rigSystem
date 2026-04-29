from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.system.comp_prepScene import PrepSceneComponent
from src.components.comp_importModel import ImportModelComponent
from src import components
from src.components.fileImport import GuideFileImport
from src.components.generator.control import ControlGenerator
from src.components.jointRenderer import JointRenderer
from src.rig.context import Context

from src.lib.naming import Name

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

placer = components.PlacerComponent(Name("placer"))
builder.modules.append(placer)

# root = components.SimpleComponent(Name("root", side="m"))
# root.inputs["parent_ws"].connect(placer.outputs["placer_ws"])
# builder.modules.append(root)
#
# spine = components.HMSpineComponent(Name("spine", side="m"))
# spine.inputs["parent_ws"].connect(root.outputs["control_ws"])

# builder.modules.append(spine)

for side in "lr":
    clavicle = ControlGenerator(Name("clavicle", side=side))
    clavicle.in_parent_mtx.connect(placer.output_mtx)
    builder.modules.append(clavicle)

    clavicle_output = JointRenderer(clavicle.name.replace(extra="skin"))
    clavicle_output.external_structure = clavicle.structure
    clavicle_output.input.connect(clavicle.out_world_mtx, dst_index=0)
    clavicle_output.nice_name = clavicle.name
    clavicle_output.for_skinning = True
    builder.add_module(clavicle_output)

    # leg = components.BipedLeg("leg", side)
    # leg.inputs["parent_ws"].connect(spine.outputs["joints_ws"], 0)
    # leg.inputs["placer_ws"].connect(placer.outputs["placer_ws"])
    # leg.pole_vector_distance = 20
    # builder.modules.append(leg)

    arm = biped_arm.BipedArm(Name("arm", side=side))
    arm.in_global.connect(placer.output_mtx)
    arm.in_parent.connect(clavicle.out_world_mtx)
    builder.modules.append(arm)

    # leg = biped_arm.BipedArm("leg", side)
    # leg.fk.inputs["parent_mtx"].connect(clavicle.outputs["control_ws"])
    # leg.fk.inputs["worldspace_mtx"].connect(placer.outputs["placer_ws"])
    # builder.modules.append(leg)


def run(stages: tuple[str] = STAGES_BUILD_FULL):
    builder.stages = stages
    # builder.parallel_stages = ["load_guide_data", "load_build_data", "load_deformer_data"]

    monitor = Monitor(builder)
    builder.run()
