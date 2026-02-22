from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.system.comp_prepScene import PrepSceneComponent
from src.components.comp_importModel import ImportModelComponent
from src.components.comp_placer import PlacerComponent
from src.components.comp_simple import SimpleComponent
from src.rig.context import Context

STAGES_BUILD_FULL = ("prepare", "connect", "load_guide_data", "build_guides", "build", "cleanup")
STAGES_BUILD_GUIDE = ("prepare", "load_guide_data", "build_guides")

builder = Builder("CharAndre")
builder.context = Context("andre", r"P:\AndreJukeBox\assets", "character")

builder.modules.append(PrepSceneComponent("prepScene"))

import_model = ImportModelComponent("importModel")
import_model.path = r"P:\AndreJukeBox\assets\character\andre\model\andre_model.ma"
builder.modules.append(import_model)

placer = PlacerComponent("placer")
builder.modules.append(placer)

root = SimpleComponent(f"root")
root.inputs["placer_ws"] << placer.outputs["placer_ws"]
builder.modules.append(root)


def run(stages: tuple[str] = STAGES_BUILD_FULL):
    builder.stages = stages
    builder.parallel_stages = ["load_guide_data", "load_build_data", "load_deformer_data"]

    monitor = Monitor(builder)
    builder.run()
