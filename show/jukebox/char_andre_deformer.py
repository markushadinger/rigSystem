from src.architecture.builder import Builder
from src.architecture.builder_monitor import Monitor

from src.components.prepScene import PrepSceneComponent
from src.components.group import Group
from src.components.fileImport import ModelFileImport
from src.components.fileImport import MayaFileImport

from src.components.control import ControlGenerator
from src.components.jointRenderer import JointRenderer
from src.components.matrixInverse import MatrixInverse
from src.components.matricesMult import MatricesMult
from src.components.piston import Piston
from src.components.matricesConstraint import MatricesConstraint
from src.assembly.biped_spine import BipedSpine
from src.assembly.biped_leg import BipedLeg
from src.assembly.biped_neck import BipedNeck
from src.assembly.biped_finger import BipedFinger
from src.components.ribbon import RibbonSkin

from src.components.skinClusterImport import SkinClusterImport
from src.lib.nodes import Node
from src.rig.context import Context

from src.lib.naming import Name
from src.rig.controls import shape

from src.assembly import biped_arm
from src.rig.module.deferred_plug import DeferredPlug

STAGES_BUILD_FULL = (
    "prepare",
    "load_files",
    "connect",
    "build",
    "cleanup",
    "import_deformer",
    "tpose"
)


class Rig(Builder):

    def __init__(self):
        super().__init__("CharAndre")

        self.context = Context("andre", r"P:\AndreJukeBox\assets", "character")

        prep_component = PrepSceneComponent(Name("prepScene"))
        self.modules.append(prep_component)

        rig_component = Group(Name("rig"))
        self.add_module(rig_component)

        import_skeleton = MayaFileImport(Name("importSkeleton"))
        import_skeleton.path = self.context.skeleton_path()
        import_skeleton.version = -1
        import_skeleton.category_name = Name("skeleton")
        import_skeleton.parent_node = rig_component.node
        self.modules.append(import_skeleton)

        import_model = ModelFileImport(Name("importModel"))
        import_model.path = self.context.asset_path() / "model" / "andre_model.ma"
        import_model.version = -1
        import_model.category_name = Name("model")
        import_model.parent_node = rig_component.node
        self.modules.append(import_model)

        skin_cluster_import = SkinClusterImport(Name("skinClusterImport"))
        skin_cluster_import.path = self.context.get_deformer_path()
        skin_cluster_import.meshes = import_model.meshes
        self.add_module(skin_cluster_import)

        # neck
        neck_twist = Piston(Name("neckTwist", "c"))
        neck_twist.input_a.connect_deferred(Node(f"neck_c_0_skn").worldMatrix[0])
        neck_twist.input_b.connect_deferred(Node(f"neck_c_end_skn").worldMatrix[0])
        neck_twist.sample_count = 3
        neck_twist.aim_axis = "y"
        neck_twist.up_axis = "x"
        self.add_module(neck_twist)

        neck_ribbon = RibbonSkin(Name("neckRibbon", "c"))
        neck_ribbon.in_mtxs.connect_deferred(neck_twist.output_mtxs)
        neck_ribbon.sample_points = 4
        neck_ribbon.u_knot_count = 5
        neck_ribbon.degree = 2
        self.add_module(neck_ribbon)

        neck_constraint = MatricesConstraint(Name("neckTwistDrive", "c"))
        neck_constraint.input.connect_deferred(neck_ribbon.out_mtxs)
        neck_constraint.nodes = [
            Node(f"neck_c_twist0_skn"),
            Node(f"neck_c_twist1_skn"),
            Node(f"neck_c_twist2_skn"),
            Node(f"neck_c_twist3_skn")
        ]
        self.add_module(neck_constraint)

        # arms
        for side in "lr":
            upper_twist = Piston(Name("armTwistUpper", side))
            upper_twist.input_a.connect_deferred(Node(f"clavicle_{side}_end_skn").worldMatrix[0])
            upper_twist.input_b.connect_deferred(Node(f"arm_{side}_elbow_skn").worldMatrix[0])
            upper_twist.sample_count = 5
            self.add_module(upper_twist)

            upper_constrain = MatricesConstraint(Name("armTwistUpperConst", side))
            upper_constrain.input.connect_deferred(upper_twist.output_mtxs)
            upper_constrain.nodes = [
                Node(f"arm_{side}_upper0_skn"),
                Node(f"arm_{side}_upper1_skn"),
                Node(f"arm_{side}_upper2_skn"),
                Node(f"arm_{side}_upper3_skn"),
                Node(f"arm_{side}_upper4_skn")
            ]
            self.add_module(upper_constrain)

            lower_twist = Piston(Name("armTwistLower", side))
            lower_twist.input_a.connect_deferred(Node(f"arm_{side}_upper4_skn").worldMatrix[0])
            lower_twist.input_b.connect_deferred(Node(f"arm_{side}_wrist_skn").worldMatrix[0])
            lower_twist.sample_count = 5
            self.add_module(lower_twist)

            lower_constrain = MatricesConstraint(Name("armTwistLowerConst", side))
            lower_constrain.input.connect_deferred(lower_twist.output_mtxs)
            lower_constrain.nodes = [
                Node(f"arm_{side}_lower0_skn"),
                Node(f"arm_{side}_lower1_skn"),
                Node(f"arm_{side}_lower2_skn"),
                Node(f"arm_{side}_lower3_skn"),
                Node(f"arm_{side}_lower4_skn")
            ]
            self.add_module(lower_constrain)

        # legs
        for side in "lr":
            upper_twist = Piston(Name("legTwistUpper", side))
            upper_twist.input_a.connect_deferred(Node(f"hip_{side}_skn").worldMatrix[0])
            upper_twist.input_b.connect_deferred(Node(f"leg_{side}_knee_skn").worldMatrix[0])
            upper_twist.sample_count = 5
            self.add_module(upper_twist)

            upper_constrain = MatricesConstraint(Name("legTwistUpperConst", side))
            upper_constrain.input.connect_deferred(upper_twist.output_mtxs)
            upper_constrain.nodes = [
                Node(f"leg_{side}_upper0_skn"),
                Node(f"leg_{side}_upper1_skn"),
                Node(f"leg_{side}_upper2_skn"),
                Node(f"leg_{side}_upper3_skn"),
                Node(f"leg_{side}_upper4_skn")
            ]
            self.add_module(upper_constrain)

            lower_twist = Piston(Name("legTwistLower", side))
            lower_twist.input_a.connect_deferred(Node(f"leg_{side}_upper4_skn").worldMatrix[0])
            lower_twist.input_b.connect_deferred(Node(f"leg_{side}_ankle_skn").worldMatrix[0])
            lower_twist.sample_count = 5
            self.add_module(lower_twist)

            lower_constrain = MatricesConstraint(Name("legTwistLowerConst", side))
            lower_constrain.input.connect_deferred(lower_twist.output_mtxs)
            lower_constrain.nodes = [
                Node(f"leg_{side}_lower0_skn"),
                Node(f"leg_{side}_lower1_skn"),
                Node(f"leg_{side}_lower2_skn"),
                Node(f"leg_{side}_lower3_skn"),
                Node(f"leg_{side}_lower4_skn")
            ]
            self.add_module(lower_constrain)

    def start_build(self, stages: tuple[str] = STAGES_BUILD_FULL):
        self.stages = stages
        monitor = Monitor(self)
        self.run()
