import maya.cmds as cmds
import math
import json
import os

CTRL_LIB = "ControlShape"  # Folder where controlShapes are located

###########
##Helper Function
###########
def get_distance_between_locators(locator1, locator2):
    """Calculate the distance between two locators."""
    pos1 = cmds.xform(locator1, query=True, worldSpace=True, translation=True)
    pos2 = cmds.xform(locator2, query=True, worldSpace=True, translation=True)

    distance = math.sqrt(
        (pos2[0] - pos1[0])**2 +
        (pos2[1] - pos1[1])**2 +
        (pos2[2] - pos1[2])**2
    )
    return distance

    # Helper function for creating locators

def deferred_execution(window,Nextfunction):
    print("deffered")
    cmds.deleteUI(window)
    cmds.evalDeferred(Nextfunction)

def create_locator(name, translate_x, translate_y, translate_z, scaleV):
    loc = cmds.spaceLocator(name=name)[0]
    ratio = (get_distance_between_locators("loc_base", "loc_top"))/180
    params = (  (f"{loc}.translateX", translate_x),
                (f"{loc}.translateY", translate_y),
                (f"{loc}.translateZ", translate_z),
                (f"{loc}Shape.overrideEnabled", 1),
                (f"{loc}Shape.overrideColor", 21)
             )
    cmds.scale(scaleV * ratio, scaleV * ratio, scaleV * ratio, loc, relative=True)

    for name, value in params:
        cmds.setAttr(name, value)
        cmds.select(clear=True)
    return loc

def symmetrize_locator(left_locator, right_locator_name):
    """Create and symmetrize the right locator based on the left one."""
    try:
        # Duplicate the locator
        duplicated_locator = cmds.duplicate(left_locator, renameChildren=True)[0]

        # Ensure the correct name is applied
        if cmds.objExists(right_locator_name):
            cmds.delete(right_locator_name)  # Clean up any previous conflicts
        duplicated_locator = cmds.rename(duplicated_locator, right_locator_name)

        # Symmetrize by inverting the X position
        current_x = cmds.getAttr(f"{duplicated_locator}.translateX")
        inverted_x = -current_x
        cmds.setAttr(f"{duplicated_locator}.translateX", inverted_x)

        print(f"Symmetrized {left_locator} to {right_locator_name}")
        return duplicated_locator

    except Exception as e:
        print(f"Error symmetrizing {left_locator} to {right_locator_name}: {e}")

def symmetrize(parts):
    for part in parts:
        symmetrize_locator(f"loc_left_{part}", f"loc_right_{part}") 

def create_joint_chain(locator_list, suffix=""):
    """Crée des joints basés sur une liste de locators."""
    for locator_name in locator_list:
        if cmds.objExists(locator_name):
            locator_pos = cmds.xform(locator_name, query=True, translation=True, worldSpace=True)
            joint_name = "joint_" + locator_name.replace("loc_", "") + suffix
            cmds.joint(position=locator_pos, radius=4, name=joint_name)
            cmds.select(clear=True)
            print(f"Joint {joint_name} created at the position of {locator_name}")
        else:
            cmds.warning(f"Locator {locator_name} not found.")

def adjust_joint_radius(joint_list, radius):
    """Ajuste le rayon des joints dans une liste."""
    for joint_name in joint_list:
        if cmds.objExists(joint_name):
            cmds.setAttr(f"{joint_name}.radius", radius)
        else:
            cmds.warning(f"Joint {joint_name} not found.")

def parent_joints(parenting_rules):
    """Parent les joints basés sur des règles."""
    for child, parent in parenting_rules:
        if cmds.objExists(child) and cmds.objExists(parent):
            cmds.parent(child, parent)
        else:
            cmds.warning(f"Parenting failed for {child} -> {parent}.")

def orient_joint(joint_list, orientation="xyz", secondary_axis="yup", zero_scale_orient=True, children=False):
    """Oriente les joints spécifiés."""
    for joint in joint_list:
        if cmds.objExists(joint):
            cmds.joint(
                joint, edit=True, orientJoint=orientation,
                secondaryAxisOrient=secondary_axis,
                zeroScaleOrient=zero_scale_orient,
                children=children
            )
        else:
            cmds.warning(f"Joint {joint} not found.")

def thumb_orientation(joint_name):
   
    # Désélectionner tout
    cmds.select(clear=True)
    
    # Sélectionner 'joint_left_thumb_1'
    cmds.select({joint_name}, replace=True)
    
    # Activer l'affichage des axes locaux de rotation
    mel.eval("ToggleLocalRotationAxes")
    
    # Ajuster la vue
    cmds.viewFit()
    
    # Activer l'outil de rotation
    cmds.setToolTo("Rotate")
    cmds.manipRotateContext("Rotate", edit=True, mode=0)
    
    # Mettre en surbrillance 'joint_left_thumb_1'
    cmds.hilite({joint_name}, replace=True)
    
    # Sélectionner l'attribut 'rotateAxis' de 'joint_left_thumb_1'
    cmds.select(f"{joint_name}.rotateAxis", replace=True)

def create_controller_from_file(file_name: str, directory: str = CTRL_LIB):
    """Creates a Maya controller from a JSON file describing its shape."""
    # Load the data from the JSON file
    user_script_dir = cmds.internalVar(userScriptDir=True)
    file_path = f"{user_script_dir}{directory}/{file_name}.shape"
    try:
        with open(file_path, 'r') as file:
            shape_data = json.load(file)
    except Exception as e:
        cmds.error(f"Error reading the JSON file: {e}")
        return
    
    # Iterate through the shapes in the file
    for shape_name, shape_attributes in shape_data.items():
        # Create a NURBS curve
        cvs = shape_attributes.get("cvs", [])
        knots = shape_attributes.get("knots", [])
        degree = shape_attributes.get("degree", 3)
        form = shape_attributes.get("form", 0)  # 0: Open, 1: Closed, 3: Periodic
        
        # Create the curve using the data
        curve = cmds.curve(p=[tuple(cv[:3]) for cv in cvs], k=knots, d=degree)
        
        # Adjust the shape based on its properties (e.g., overrideColorRGB)
        if "overrideColorRGB" in shape_attributes:
            color = shape_attributes["overrideColorRGB"]
            cmds.setAttr(f"{curve}.overrideEnabled", 1)
            cmds.setAttr(f"{curve}.overrideRGBColors", 1)
            cmds.setAttr(f"{curve}.overrideColorR", color[0])
            cmds.setAttr(f"{curve}.overrideColorG", color[1])
            cmds.setAttr(f"{curve}.overrideColorB", color[2])
        
        # Rename the shape with the specified name
        curve = cmds.rename(curve, shape_name)
        print(f"Controller created: {curve}")


#########
##Function
########

def create_leg_locators():
    locator1 = "loc_base"
    locator2 = "loc_top"

    # Calculate the distance
    distance = get_distance_between_locators(locator1, locator2)
    print(f"Distance between locators: {distance}")

    # Create Hips Locator
    distance_hips = distance / 2
    loc_hips = cmds.spaceLocator(name="loc_Hips")[0]
    cmds.setAttr(f"{loc_hips}.translateY", distance_hips)
    cmds.setAttr(f"{loc_hips}Shape.overrideEnabled", 1)
    cmds.setAttr(f"{loc_hips}Shape.overrideColor", 21)
    cmds.scale(10, 10, 10, loc_hips, relative=True)
    cmds.select(clear=True)

    # Create Left Leg Locators
    create_locator("loc_left_thig", distance / 18, distance / 1.9, 0, 10)
    create_locator("loc_left_leg", distance / 16.5, distance / 3.6, distance / -66.6, 10)
    create_locator("loc_left_foot", distance / 14.17, distance / 18.44, distance / -22.5, 10)
    create_locator("loc_left_toes", distance / 14.17, distance / 103.8, distance / 52.2, 10)
    create_locator("loc_left_end", distance / 14.17, distance / 103.8, distance / 17.25, 10)

def symmetrize_leg():
    symmetrize(("thig", "leg", "foot", "toes", "end"))

def create_arm_locator(distance):
    # Create Left arm Locators
    create_locator("loc_left_shoulder", distance / 12.5, distance / 1.22, distance / -46.15, 10)
    create_locator("loc_left_forearm", distance / 4.4, distance / 1.25, distance / -36.73, 10)
    create_locator("loc_left_hand", distance / 2.7, distance / 1.23, distance / 114.95, 10)

    create_locator("loc_left_pinkie_1", distance / 2.7, distance / 1.22, distance / -656.93, 1)
    create_locator("loc_left_pinkie_2", distance / 2.46, distance / 1.23, distance / -156.11, 1)
    create_locator("loc_left_pinkie_3", distance / 2.37, distance / 1.23, distance / -124.13, 1)

    create_locator("loc_left_ring_1", distance / 2.66, distance / 1.22, distance / 188.48, 1)
    create_locator("loc_left_ring_2", distance / 2.45, distance / 1.22, distance / 214.54, 1)
    create_locator("loc_left_ring_3", distance / 2.31, distance / 1.22, distance / 268.255, 1)

    create_locator("loc_left_middle_1", distance / 2.66, distance / 1.22, distance / 64.31, 1)
    create_locator("loc_left_middle_2", distance / 2.45, distance / 1.22, distance / 60.34, 1)
    create_locator("loc_left_middle_3", distance / 2.29, distance / 1.22, distance / 60.34, 1)

    create_locator("loc_left_index_1", distance / 2.65, distance / 1.22, distance / 38.46, 1)
    create_locator("loc_left_index_2", distance / 2.45, distance / 1.22, distance / 34.38, 1)
    create_locator("loc_left_index_3", distance / 2.32, distance / 1.23, distance / 33.09, 1)

    create_locator("loc_left_thumb_1", distance / 2.7, distance / 1.24, distance / 36.42, 1)
    create_locator("loc_left_thumb_2", distance / 2.59, distance / 1.24, distance / 25.07, 1)
    create_locator("loc_left_thumb_3", distance / 2.49, distance / 1.25, distance / 20.48, 1)

def symmetrize_arm():
    symmetrize(("shoulder", "forearm", "hand",
                "pinkie_1", "pinkie_2", "pinkie_3",
                "ring_1", "ring_2", "ring_3",
                "middle_1", "middle_2", "middle_3",
                "index_1", "index_2", "index_3",
                "thumb_1", "thumb_2", "thumb_3",))

def create_spine_to_head_locators(distance):
        
    create_locator("loc_Spine_1", 0, distance / 1.7, 0, 10)
    create_locator("loc_Spine_2", 0, distance / 1.54, 0, 10)
    create_locator("loc_Spine_3", 0, distance / 1.38, 0, 10)
    create_locator("loc_Spine_4", 0, distance / 1.2, distance / -46.15, 10)
    create_locator("loc_neck", 0,distance / 1.13, distance / 814.47, 10)
    create_locator("loc_head", 0,distance / 1.071, distance / 106.13, 10)

    # Create clavicles
    create_locator("loc_clavicle_right", distance / -55.197, distance / 1.224, distance / 124.602, 10)
    create_locator("loc_clavicle_left", distance / 55.197, distance / 1.224, distance / 124.602, 10)

    # Create pectorals
    create_locator("loc_pec_right", distance / -16.912, distance / 1.363, distance / 12.961, 10)
    create_locator("loc_pec_left", distance / 16.912, distance / 1.363, distance / 12.961, 10)

def run_leg():
    create_leg_locators()
    show_window_symLeg()
    
def run_symleg():
    symmetrize_leg()
    create_spine_to_head_locators(get_distance_between_locators("loc_base", "loc_top"))
    show_window_armL()

def run_arm():
    create_arm_locator(get_distance_between_locators("loc_base", "loc_top"))
    show_window_symArm()

def run_symArm():
    symmetrize_arm()
    show_window_CreaJoint()

def CreaJoint():
    # Select all the locators
    cmds.select('loc_right_thumb_3', 'loc_right_thumb_2', 'loc_right_thumb_1', 'loc_right_index_3', 
            'loc_right_index_2', 'loc_right_index_1', 'loc_right_middle_3', 'loc_right_middle_2', 
            'loc_right_middle_1', 'loc_right_ring_3', 'loc_right_ring_2', 'loc_right_ring_1', 
            'loc_right_pinkie_3', 'loc_right_pinkie_2', 'loc_right_pinkie_1', 'loc_right_hand', 
            'loc_right_forearm', 'loc_right_shoulder', 'loc_left_thumb_3', 'loc_left_thumb_2', 
            'loc_left_thumb_1', 'loc_left_index_3', 'loc_left_index_2', 'loc_left_index_1', 
            'loc_left_middle_3', 'loc_left_middle_2', 'loc_left_middle_1', 'loc_left_ring_3', 
            'loc_left_ring_2', 'loc_left_ring_1', 'loc_left_pinkie_3', 'loc_left_pinkie_2', 
            'loc_left_pinkie_1', 'loc_left_hand', 'loc_left_forearm', 'loc_left_shoulder', 'loc_Spine_4', 
            'loc_Spine_3', 'loc_Spine_2', 'loc_Spine_1', 'loc_neck', 'loc_head', 'loc_right_end', 
            'loc_right_toes', 'loc_right_foot', 'loc_right_leg', 'loc_right_thig', 'loc_left_end', 
            'loc_left_toes', 'loc_left_foot', 'loc_left_leg', 'loc_left_thig', 'loc_Hips', 'loc_top', 
            'loc_base', 'loc_clavicle_right', 'loc_clavicle_left', 'loc_pec_right', 'loc_pec_left')

    # Group the locators
    cmds.Group(0, 1, 1)

    # Rename the group
    cmds.rename('group1', 'Locator_grp')

        # Locator lists
    main_locators = [
        "loc_right_thumb_3", "loc_right_thumb_2", "loc_right_thumb_1", "loc_right_index_3", "loc_right_index_2", "loc_right_index_1", 
        "loc_right_middle_3", "loc_right_middle_2", "loc_right_middle_1", "loc_right_ring_3", "loc_right_ring_2", "loc_right_ring_1", 
        "loc_right_pinkie_3", "loc_right_pinkie_2", "loc_right_pinkie_1", "loc_right_hand", "loc_right_forearm", "loc_right_shoulder", 
        "loc_left_thumb_3", "loc_left_thumb_2", "loc_left_thumb_1", "loc_left_index_3", "loc_left_index_2", "loc_left_index_1", 
        "loc_left_middle_3", "loc_left_middle_2", "loc_left_middle_1", "loc_left_ring_3", "loc_left_ring_2", "loc_left_ring_1", 
        "loc_left_pinkie_3", "loc_left_pinkie_2", "loc_left_pinkie_1", "loc_left_hand", "loc_left_forearm", "loc_left_shoulder", 
        "loc_Spine_4", "loc_Spine_3", "loc_Spine_2", "loc_Spine_1", "loc_neck", "loc_head", "loc_right_end", "loc_right_toes", 
        "loc_right_foot", "loc_right_leg", "loc_right_thig", "loc_left_end", "loc_left_toes", "loc_left_foot", "loc_left_leg", "loc_left_thig", 
        "loc_Hips", "loc_clavicle_right", "loc_clavicle_left", "loc_pec_right", "loc_pec_left"
    ]
    ik_locators = [
        "loc_right_hand", "loc_right_forearm", "loc_right_shoulder", "loc_left_hand", "loc_left_forearm", "loc_left_shoulder", 
        "loc_right_foot", "loc_right_leg", "loc_right_thig", "loc_left_foot", "loc_left_leg", "loc_left_thig", "loc_right_end", "loc_right_toes", "loc_left_end", "loc_left_toes"
    ]
    fk_locators = [
        "loc_right_hand", "loc_right_forearm", "loc_right_shoulder", "loc_left_hand", "loc_left_forearm", "loc_left_shoulder", 
        "loc_right_foot", "loc_right_leg", "loc_right_thig", "loc_right_end", "loc_right_toes", "loc_left_foot", "loc_left_end", "loc_left_toes", "loc_left_leg", "loc_left_thig"
    ]

    # Create joints for each category
    create_joint_chain(main_locators)
    create_joint_chain(ik_locators, suffix="_IK")
    create_joint_chain(fk_locators, suffix="_FK")

    # Adjust radius
    adjust_joint_radius([
        "joint_right_pinkie_3", "joint_right_hand", "joint_right_thumb_1", "joint_right_thumb_2", "joint_right_thumb_3", 
        "joint_right_index_1", "joint_right_index_2", "joint_right_index_3", "joint_right_middle_1", "joint_right_middle_2", "joint_right_middle_3", 
        "joint_right_ring_1", "joint_right_ring_2", "joint_right_ring_3", "joint_right_pinkie_1", "joint_right_pinkie_2", 
        "joint_left_pinkie_3", "joint_left_hand", "joint_left_thumb_1", "joint_left_thumb_2", "joint_left_thumb_3", 
        "joint_left_index_1", "joint_left_index_2", "joint_left_index_3", "joint_left_middle_1", "joint_left_middle_2", "joint_left_middle_3", 
        "joint_left_ring_1", "joint_left_ring_2", "joint_left_ring_3", "joint_left_pinkie_1", "joint_left_pinkie_2"
    ], 1)

    # Parent joints
    parenting_rules = [
        ("joint_right_thumb_3", "joint_right_thumb_2"),
        ("joint_right_thumb_2", "joint_right_thumb_1"),
        ("joint_right_index_3", "joint_right_index_2"),
        ("joint_right_index_2", "joint_right_index_1"),
        ("joint_right_middle_3", "joint_right_middle_2"),
        ("joint_right_middle_2", "joint_right_middle_1"),
        ("joint_right_ring_3", "joint_right_ring_2"),
        ("joint_right_ring_2", "joint_right_ring_1"),
        ("joint_right_pinkie_3", "joint_right_pinkie_2"),
        ("joint_right_pinkie_2", "joint_right_pinkie_1"),
        ("joint_right_thumb_1", "joint_right_hand"),
        ("joint_right_index_1", "joint_right_hand"),
        ("joint_right_middle_1", "joint_right_hand"),
        ("joint_right_ring_1", "joint_right_hand"),
        ("joint_right_pinkie_1", "joint_right_hand"),
        ("joint_right_hand", "joint_right_forearm"),
        ("joint_right_forearm", "joint_right_shoulder"),
        ("joint_right_hand_IK", "joint_right_forearm_IK"),
        ("joint_right_forearm_IK", "joint_right_shoulder_IK"),
        ("joint_right_hand_FK", "joint_right_forearm_FK"),
        ("joint_right_forearm_FK", "joint_right_shoulder_FK"),
        ("joint_left_thumb_3", "joint_left_thumb_2"),
        ("joint_left_thumb_2", "joint_left_thumb_1"),
        ("joint_left_index_3", "joint_left_index_2"),
        ("joint_left_index_2", "joint_left_index_1"),
        ("joint_left_middle_3", "joint_left_middle_2"),
        ("joint_left_middle_2", "joint_left_middle_1"),
        ("joint_left_ring_3", "joint_left_ring_2"),
        ("joint_left_ring_2", "joint_left_ring_1"),
        ("joint_left_pinkie_3", "joint_left_pinkie_2"),
        ("joint_left_pinkie_2", "joint_left_pinkie_1"),
        ("joint_left_thumb_1", "joint_left_hand"),
        ("joint_left_index_1", "joint_left_hand"),
        ("joint_left_middle_1", "joint_left_hand"),
        ("joint_left_ring_1", "joint_left_hand"),
        ("joint_left_pinkie_1", "joint_left_hand"),
        ("joint_left_hand", "joint_left_forearm"),
        ("joint_left_forearm", "joint_left_shoulder"),
        ("joint_left_hand_IK", "joint_left_forearm_IK"),
        ("joint_left_forearm_IK", "joint_left_shoulder_IK"),
        ("joint_left_hand_FK", "joint_left_forearm_FK"),
        ("joint_left_forearm_FK", "joint_left_shoulder_FK"),
        ("joint_Spine_4", "joint_Spine_3"),
        ("joint_Spine_3", "joint_Spine_2"),
        ("joint_Spine_2", "joint_Spine_1"),
        ("joint_Spine_1", "joint_Hips"),
        ("joint_neck", "joint_Spine_4"),
        ("joint_head", "joint_neck"),
        ("joint_right_toes", "joint_right_foot"),
        ("joint_right_foot", "joint_right_leg"),
        ("joint_right_leg", "joint_right_thig"),
        ("joint_left_toes", "joint_left_foot"),
        ("joint_left_foot", "joint_left_leg"),
        ("joint_left_leg", "joint_left_thig"),
        ("joint_right_thig", "joint_Hips"),
        ("joint_left_thig", "joint_Hips"),
        ("joint_left_end", "joint_left_toes"),
        ("joint_right_end", "joint_right_toes"),  
        ("joint_clavicle_right", "joint_Spine_4"),
        ("joint_clavicle_left", "joint_Spine_4"),
        ("joint_pec_right", "joint_clavicle_right"),
        ("joint_pec_left", "joint_clavicle_left"),
        ("joint_left_shoulder", "joint_clavicle_left"),
        ("joint_right_shoulder", "joint_clavicle_right"),
        ("joint_right_shoulder_IK", "joint_clavicle_right"),
        ("joint_right_shoulder_FK", "joint_clavicle_right"),
        ("joint_left_shoulder_IK", "joint_clavicle_left"),
        ("joint_left_shoulder_FK", "joint_clavicle_left"),
        ("joint_right_toes_IK", "joint_right_foot_IK"),
        ("joint_right_foot_IK", "joint_right_leg_IK"),
        ("joint_right_leg_IK", "joint_right_thig_IK"),
        ("joint_left_toes_IK", "joint_left_foot_IK"),
        ("joint_left_foot_IK", "joint_left_leg_IK"),
        ("joint_left_leg_IK", "joint_left_thig_IK"),
        ("joint_right_thig_IK", "joint_Hips"),
        ("joint_left_thig_IK", "joint_Hips"),
        ("joint_left_end_IK", "joint_left_toes_IK"),
        ("joint_right_end_IK", "joint_right_toes_IK"),
        ("joint_right_toes_FK", "joint_right_foot_FK"),
        ("joint_right_foot_FK", "joint_right_leg_FK"),
        ("joint_right_leg_FK", "joint_right_thig_FK"),
        ("joint_left_toes_FK", "joint_left_foot_FK"),
        ("joint_left_foot_FK", "joint_left_leg_FK"),
        ("joint_left_leg_FK", "joint_left_thig_FK"),
        ("joint_right_thig_FK", "joint_Hips"),
        ("joint_left_thig_FK", "joint_Hips"),
        ("joint_left_end_FK", "joint_left_toes_FK"),
        ("joint_right_end_FK", "joint_right_toes_FK"),
    ]

    parent_joints(parenting_rules)
    orient_joint_groups()

def orient_joint_groups():
    """Oriente les groupes de joints selon les règles du MEL original."""
    # Hips to Head
    orient_joint(
        ["joint_Hips", "joint_Spine_1", "joint_Spine_2", "joint_Spine_3", "joint_Spine_4", "joint_neck", "joint_head"],
        orientation="yxz", secondary_axis="xup", children=True
    )
    # Head
    orient_joint(["joint_head"], orientation="none", children=True)

    # Left Arm
    orient_joint(
        ["joint_clavicle_left", "joint_left_shoulder", "joint_left_forearm", "joint_left_hand"],
        orientation="xyz", secondary_axis="yup", children=True
    )
    orient_joint(["joint_left_hand"], orientation="none", children=True)

    # Left Fingers
    for finger in ["thumb", "index", "middle", "ring", "pinkie"]:
        orient_joint(
            [f"joint_left_{finger}_1", f"joint_left_{finger}_2", f"joint_left_{finger}_3"],
            orientation="xyz", secondary_axis="yup", children=True
        )
    orient_joint(
        ["joint_left_pinkie_3", "joint_left_ring_3", "joint_left_middle_3", "joint_left_index_3"],
        orientation="none"
    )

    # Right Arm
    orient_joint(
        ["joint_clavicle_right", "joint_right_shoulder", "joint_right_forearm", "joint_right_hand"],
        orientation="xyz", secondary_axis="yup", children=True
    )
    orient_joint(["joint_right_hand"], orientation="none", children=True)

    # Right Fingers
    for finger in ["thumb", "index", "middle", "ring", "pinkie"]:
        orient_joint(
            [f"joint_right_{finger}_1", f"joint_right_{finger}_2", f"joint_right_{finger}_3"],
            orientation="xyz", secondary_axis="yup", children=True
        )
    orient_joint(
        ["joint_right_pinkie_3", "joint_right_ring_3", "joint_right_middle_3", "joint_right_index_3"],
        orientation="none"
    )

    # Legs (IK, FK, and default)
    orient_joint(
        [
            "joint_right_thig_IK", "joint_right_leg_IK", "joint_right_foot_IK", "joint_right_toes_IK", "joint_right_end_IK",
            "joint_left_thig_IK", "joint_left_leg_IK", "joint_left_foot_IK", "joint_left_toes_IK", "joint_left_end_IK",
            "joint_right_thig_FK", "joint_right_leg_FK", "joint_right_foot_FK", "joint_right_toes_FK", "joint_right_end_FK",
            "joint_left_thig_FK", "joint_left_leg_FK", "joint_left_foot_FK", "joint_left_toes_FK", "joint_left_end_FK",
            "joint_left_thig", "joint_left_leg", "joint_left_foot", "joint_left_toes", "joint_left_end",
            "joint_right_thig", "joint_right_leg", "joint_right_foot", "joint_right_toes", "joint_right_end"
        ],
        orientation="yxz", secondary_axis="xup", children=True
    )
    # End joints
    orient_joint(
        ["joint_right_end", "joint_left_end", "joint_left_end_FK", "joint_right_end_FK", "joint_left_end_IK", "joint_right_end_IK"],
        orientation="none"
    )

    thumb_orientation("joint_left_thumb_1")
    show_window_Left_Thumb1()

def Left_Thumb2():
    thumb_orientation("joint_left_thumb_2")
    show_window_Left_Thumb2()

def Right_Thumb1():
    thumb_orientation("joint_right_thumb_1")
    show_window_Right_Thumb1()

def Right_Thumb2():
    thumb_orientation("joint_right_thumb_2")
    show_window_Right_Thumb2()

def Control_Creation():
# Ajuster la vue pour inclure tous les objets
cmds.viewFit("persp", all=True )

# Masquer les Locators
cmds.hide("Locator_grp")

# OrientJoint L/R_Thumbs_3 
cmds.select("joint_right_thumb_3", r=True)
cmds.joint(e=True, oj="none", ch=True, zso=True)
cmds.select(clear=True)

cmds.select("joint_left_thumb_3", r=True)
cmds.joint(e=True, oj="none", ch=True, zso=True)
cmds.select(clear=True)

# Créer le contrôleur Root
create_controller_from_file("zoo_shapes\godnode_reg")

# Select the objects
cmds.select("godnode_regShape1", "godnode_regShape")

# Apply transformations and freeze scale
cmds.makeIdentity(apply=True, translate=True, rotate=True, scale=True, normal=False, preserveNormals=True)

# Select the shapes
cmds.select("godnode_regShapeShape",  "godnode_regShape1")

# Parent shapes under the same transform node
cmds.parent(r=True, shape=True)

# Select and delete the transform node
cmds.select("godnode_regShape", replace=True)
cmds.delete()
cmds.rename("godnode_regShape1", "root_Ctrl")

# Scale the objects
root_scale = 54
cmds.setAttr("root_Ctrl.scaleX", root_scale)
cmds.setAttr("root_Ctrl.scaleY", root_scale)
cmds.setAttr("root_Ctrl.scaleZ", root_scale)

# Geler les transformations
cmds.makeIdentity(apply=True, t=True, r=True, s=True, n=False)


#########
## Windows that wait User input to continue
#########

def show_window(window_name="Check_Locators_Window", 
                lbl_list=None,
                btn_lbl="Continue to Right Leg and Spine",
                cmd_var=run_leg,
                ):
    if lbl_list is None:
        lbl_list = []
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    window = cmds.window(window_name, title="Check and Proceed", widthHeight=(300, 100))

    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label="")
    for lbl in lbl_list:
        cmds.text(label=lbl)
    cmds.text(label="")
    cmds.button(label=btn_lbl, command=lambda _: deferred_execution(window,cmd_var))

    cmds.showWindow(window)

def show_window_leg():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to left Leg ",
                cmd_var=run_leg,
                )

def show_window_symLeg():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Right Leg and Spine ",
                cmd_var=run_symleg,
                )

def show_window_armL():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to left arm ",
                cmd_var=run_arm,
                ) 
 
def show_window_symArm():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to right arm ",
                cmd_var=run_symArm,
                ) 
 
def show_window_CreaJoint():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Left thumb Orientation ",
                cmd_var=CreaJoint,
                ) 

def show_window_Left_Thumb1():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Left thumb Orientation 2 ",
                cmd_var=Left_Thumb2,
                )

def show_window_Left_Thumb2():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Right thumb Orientation 1 ",
                cmd_var=Right_Thumb1,
                )

def show_window_Right_Thumb1():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Right thumb Orientation 2 ",
                cmd_var=Right_Thumb2,
                )

def show_window_Right_Thumb2():
    show_window(window_name="Check_Locators_Window", 
                lbl_list=[
                    "Check and adjust the locator positions.",
                    "Then click to proceed."
                ],
                btn_lbl="Continue to Controller Creation ",
                cmd_var=Control_Creation,
                )




# Script Beginning

# Create Locator at Base and Top
# Base Locator
base_locator = cmds.spaceLocator(name="loc_base", position=(0, 0, 0))[0]
cmds.setAttr(f"{base_locator}Shape.overrideEnabled", 1)
cmds.setAttr(f"{base_locator}Shape.overrideColor", 21)
cmds.scale(10, 10, 10, base_locator, relative=True)
cmds.select(clear=True)

# Top Locator
top_locator = cmds.spaceLocator(name="loc_top", position=(0, 0, 0))[0]
cmds.setAttr(f"{top_locator}.translateY", 180)
cmds.setAttr(f"{top_locator}Shape.overrideEnabled", 1)
cmds.setAttr(f"{top_locator}Shape.overrideColor", 21)
cmds.scale(10, 10, 10, top_locator, relative=True)
cmds.select(clear=True)

show_window_leg()











