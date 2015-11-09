import string_tools
import random

class Recipe(object):
    def __init__(self):
        self.materials = []
        self.tools = []

    def add_material(self, material):
        self.materials.append(material)

    def add_tool(self, tool):
        self.tools.append(tool)

    def create(self):
        print("Materials:")
        for material in self.materials:
            print(" - " + material.get_label())
        print();

        print("Tools:")
        for tool in self.tools:
            if tool.has_label():
                print(" - " + tool.get_label())
        print();

        print("Instructions:")
        print("1. Mix all ingredients.")
        print("2. You're done! Congratulations!")


class Material(object):
    def __init__(self, name, amount, quantity_type):
        self.name = name
        self.name_plural = string_tools.pluralize(name)
        self.amount = amount
        self.quantity_type = quantity_type

    def get_label(self):
        return self.quantity_type.get_material_label(self, self.amount)

    def equals(self, other_material):
        return self.name == other_material.name


class MaterialType(object):
    def __init__(self):
        pass


class QuantityType(object):
    def __init__(self, singular_format, pluralized_format, integer_only):
        self.singular_format = singular_format
        self.pluralized_format = pluralized_format
        self.integer_only = integer_only

    def get_material_label(self, material, amount):
        return (self.singular_format if amount == 1 else self.pluralized_format)\
            .replace("{amount}", str(amount))\
            .replace("{material}", material.name)\
            .replace("{material_plural}", material.name_plural)

    def random_amount(self):
        min = 1
        max = 10

        for i in range(5):
            if random.random() < 0.1:
                max *= random.randint(2, 5)

        if self.integer_only:
            return random.randint(min, max)

        return round(random.uniform(min, max) * 100) / 100


class Tool(object):
    def __init__(self, tool_type):
        self.tool_type = tool_type

    def has_label(self):
        return len(self.tool_type.name) > 0

    def get_label(self):
        return self.tool_type.name

    def equals(self, other_tool):
        return self.tool_type.name == other_tool.tool_type.name

class ToolType(object):
    def __init__(self, name_list=[]):
        if len(name_list) > 0:
            self.name = random.choice(name_list)
        else:
            self.name = ""

    def add_material_consuming_action(self, instruction):
        pass

    def add_material_transforming_action(self, instruction, result):
        pass

    def add_action(self, instruction):
        pass

    def add_generating_action(self, instruction, result, only_when_filled):
        pass
