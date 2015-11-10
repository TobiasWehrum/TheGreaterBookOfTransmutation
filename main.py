import random
from recipe import Recipe
from recipe import Material
from recipe import MaterialType
from recipe import QuantityType
from recipe import Tool
from recipe import ToolType


def main():
    material_names = ["elephant", "tomato", "window", "poison", "water"]

    quantity_type_countable = QuantityType("{amount} {material}", "{amount} {material_plural}", True)
    quantity_type_gram = QuantityType("{amount} gram of {material}", "{amount} grams of {material}", False)
    quantity_types = [quantity_type_countable, quantity_type_gram]

    tool_type_vessel = ToolType(["cauldron", "container", "vessel"])
    tool_type_vessel.add_material_consuming_action("Put {material} into {tool}")
    tool_type_vessel.add_simple_action("[Stir|Heat] {tool}")
    tool_type_vessel.add_simple_action("Let {tool} cool down")
    tool_type_vessel.add_generating_action("Pour out the mixture from {tool}", "{tool} mixture ({contents})", [quantity_type_gram], True)

    tool_type_smashing = ToolType(["hammer", "stone"])
    tool_type_smashing.add_material_transforming_action("Smash {material} with the {tool}", "smashed {material}")
    tool_type_smashing.add_material_transforming_action("Crack {material} with the {tool}", "cracked {material}")

    tool_types = [tool_type_vessel, tool_type_smashing]

    tool_type_default = ToolType()
    tool_type_default.add_material_consuming_action("Eat {material}")
    tool_type_default.add_simple_action("Wait[| for [a[| very| rather] [short|long] time|[1|2|3|4|5|6|7|8|9|10] [seconds|minutes|hours|days]]]")

    create_recipe(material_names, quantity_types, tool_types, tool_type_default)


def create_recipe(material_names, quantity_types, tool_types, tool_type_default):
    recipe = Recipe()

    for material_name in random.sample(material_names, min(4, len(material_names))):
        quantity_type = random.choice(quantity_types)
        amount = quantity_type.random_amount()

        recipe.add_material(Material(material_name, amount, quantity_type))

        if len(material_names) == 0:
            break

    while len(recipe.tools) < 2:
        tool = Tool(random.choice(tool_types))
        if not any(tool.equals(other_tool) for other_tool in recipe.tools):
            recipe.add_tool(tool)

    recipe.add_tool(Tool(tool_type_default))

    recipe.create()
    recipe.print()


# Only run if we are the main program, not an import.
if __name__ == "__main__": main()
