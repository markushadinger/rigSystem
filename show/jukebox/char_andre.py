from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.system.comp_prepScene import PrepSceneComponent
from src.components.comp_importModel import ImportModelComponent
from src import components
from src.rig.context import Context

STAGES_BUILD_FULL = ("prepare", "connect", "load_build_data", "build", "cleanup")
STAGES_BUILD_GUIDE = ("prepare", "load_guide_data", "build_guides")

builder = Builder("CharAndre")
builder.context = Context("andre", r"P:\AndreJukeBox\assets", "character")

builder.modules.append(PrepSceneComponent("prepScene"))

import_model = ImportModelComponent("importModel")
import_model.path = r"P:\AndreJukeBox\assets\character\andre\model\andre_model.ma"
# builder.modules.append(import_model)

placer = components.PlacerComponent("placer")
builder.modules.append(placer)

root = components.SimpleComponent(f"root")
root.inputs["parent_ws"].connect(placer.outputs["placer_ws"])
builder.modules.append(root)

spine = components.HMSpineComponent(f"spine")
spine.inputs["parent_ws"].connect(root.outputs["control_ws"])
builder.modules.append(spine)

for side in "lr":
    clavicle = components.SimpleComponent(f"clavicle_{side}")
    clavicle.inputs["parent_ws"].connect(spine.outputs["joints_ws"], -1)
    builder.modules.append(clavicle)

    arm = components.BpLimb(f"arm_{side}")
    arm.inputs["parent_ws"].connect(clavicle.outputs["control_ws"])
    builder.modules.append(arm)


def run(stages: tuple[str] = STAGES_BUILD_FULL):
    builder.stages = stages
    # builder.parallel_stages = ["load_guide_data", "load_build_data", "load_deformer_data"]

    monitor = Monitor(builder)
    builder.run()
