import json
import maya.cmds as cmds

def create_controller_from_file(file_path):
    """Crée un contrôleur Maya à partir d'un fichier JSON décrivant sa forme."""
    # Charger les données du fichier JSON
    try:
        with open(file_path, 'r') as file:
            shape_data = json.load(file)
    except Exception as e:
        cmds.error(f"Erreur lors de la lecture du fichier JSON : {e}")
        return
    
    # Parcourir les formes dans le fichier
    for shape_name, shape_attributes in shape_data.items():
        # Créer une courbe NURBS
        cvs = shape_attributes.get("cvs", [])
        knots = shape_attributes.get("knots", [])
        degree = shape_attributes.get("degree", 3)
        form = shape_attributes.get("form", 0)  # 0: Open, 1: Closed, 3: Periodic
        
        # Créer la courbe à partir des données
        curve = cmds.curve(p=[tuple(cv[:3]) for cv in cvs], k=knots, d=degree)
        
        # Ajuster la forme en fonction des propriétés (exemple : overrideColorRGB)
        if "overrideColorRGB" in shape_attributes:
            color = shape_attributes["overrideColorRGB"]
            cmds.setAttr(f"{curve}.overrideEnabled", 1)
            cmds.setAttr(f"{curve}.overrideRGBColors", 1)
            cmds.setAttr(f"{curve}.overrideColorR", color[0])
            cmds.setAttr(f"{curve}.overrideColorG", color[1])
            cmds.setAttr(f"{curve}.overrideColorB", color[2])
        
        # Renommer la forme avec le nom spécifié
        curve = cmds.rename(curve, shape_name)
        print(f"Contrôleur créé : {curve}")

# Utilisation
file_path = "circle_half_thick.json"  # Remplacez par le chemin complet si nécessaire
create_controller_from_file(file_path)
