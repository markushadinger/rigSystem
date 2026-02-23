from src.components._comp_base import Component
from src.rig.data_manager import JsonDataManager
from src.rig.module.deferred_plug import TYPE_MATRIX
from src.lib import guide
from src.rig.controls import color, control, shape
from src.lib import hierarchy

from maya import cmds
from maya.api import OpenMaya

PELVIS_FLIP_MTX = OpenMaya.MMatrix([1,0,0,0, 0,-1,0,0, 0,0,1,0, 0,0,0,1])

class HMSpineComponent(Component):
    INPUTS = {
        "placer_ws": TYPE_MATRIX,
        "parent_ws": TYPE_MATRIX,
    }

    OUTPUTS = {
        "control_ws": TYPE_MATRIX,
        "control_ls": TYPE_MATRIX,
        "control_rs": TYPE_MATRIX,
    }

    def __init__(self, name):
        super().__init__(name)

        self.guide_version:int = -1
        self.guide_data: JsonDataManager | None = None

        self.control_count:int = 5
        self.joint_count:int = 10
        self.pelvis_flip_mtx:OpenMaya.MMatrix =PELVIS_FLIP_MTX


    def prepare(self):
        super().prepare()
        self.guide_data = JsonDataManager(self.context.guide_file_path(self.name), self.guide_version)

    def load_guide_data(self):
        self.guide_data.load()

    def build_guides(self):     

        for i in self.get_indices():
            joint = guide.create_guide_joint(guide.get_name(i), self.name)
            cmds.parent(joint, str(self.structure.guides))
         
        guide_data_dict = {guide.get_name(n): m for n, m in self.guide_data.data.items()}
        print(guide_data_dict)
        hierarchy.match_nodes_to_matrices({guide.get_name(n): m for n, m in self.guide_data.data.items()})

    def build(self):        
        self.build_fk()
        self.build_hip()
        
        
        

                
    def get_indices(self) -> list[str]:
        indices = list(range(self.control_count))
        indices[-1] = "end"
        return [f"{self.name}_{i}" for i in indices]
    
    def build_fk(self):
        """
        Build FK controls for the spine. The number of controls is determined by self.control_count.
        The controls are evenly distributed along the spine joints.
        """
        
        parent_ctrl = None
        
        for i in self.get_indices():                        
            ctrl = control.build(control.get_name(i))
            shape.set_shape(ctrl, shape.scale_shape(shape.CIRCLE, 20))
            color.set_color(ctrl, color.COLOR_YELLOW)
            
            cmds.parent(ctrl, str(self.structure.controls))            
            ctrl.inOffsetMatrix.value = self.guide_data.data[i]
            
            if parent_ctrl:
                control.set_parent_control(ctrl, parent_ctrl)
            else:
                ctrl.inParentMatrix << self.inputs["parent_ws"].plug
            
            parent_ctrl = ctrl
            
    def build_hip(self):
        """
        Build hip control. The hip control is the parent of the first spine control and is used to drive the entire spine.
        """        
        
        pelvis_matrix = self.pelvis_flip_mtx * OpenMaya.MMatrix(self.guide_data.data[f"{self.name}_0"]) 
        
        ctrl = control.build(control.get_name(f"{self.name}_hip"))
        shape.set_shape(ctrl, shape.scale_shape(shape.CIRCLE, 25))
        color.set_color(ctrl, color.COLOR_PURPLE)
        
        cmds.parent(ctrl, str(self.structure.controls))
        ctrl.inOffsetMatrix.value = pelvis_matrix
        ctrl.inParentMatrix << self.inputs["parent_ws"].plug
        
            
