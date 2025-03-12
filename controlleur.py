import maya.cmds as cmds
import json
import os

CTRL_LIB = "ControlShape"  # Folder where controlShapes are located


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


# Créer le contrôleur LegFK
#L_thig
create_controller_from_file("zoo_three_dimensional/circle_half_thick")
root_scale = 9







# Création de contrôleurs de cuisse et de jambes
def create_leg_control(name, distance, color):
    leg_curve = cmds.curve(
        name=name,
        d=1,
        p=[
            (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
            (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5),
            (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5),
            (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5),
            (-0.5, -0.5, 0.5)
        ]
    )
    scale_x = distance / 9
    scale_y = distance / 6.5
    scale_z = distance / 7.8
    cmds.setAttr(f"{name}.scaleX", scale_x)
    cmds.setAttr(f"{name}.scaleY", scale_y)
    cmds.setAttr(f"{name}.scaleZ", scale_z)
    cmds.makeIdentity(apply=True, t=True, r=True, s=True, n=False)

    cmds.setAttr(f"{name}.overrideEnabled", 1)
    cmds.setAttr(f"{name}.overrideColor", color)

create_leg_control("left_thig_FK_Ctrl", distance, 9)
create_leg_control("right_thig_FK_Ctrl", distance, 28)
create_leg_control("left_leg_FK_Ctrl", distance, 9)
create_leg_control("right_leg_FK_Ctrl", distance, 28)

# Ajout des contrôleurs des pieds...
