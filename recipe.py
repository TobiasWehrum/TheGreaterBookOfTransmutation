import random


class Recipe(object):
    def __init__(self, end_product):
        self.end_product = end_product
        self.materials = []
        self.tools = []
        self.instructions = []

    def add_material(self, material):
        self.materials.append(material)

    def add_tool(self, tool):
        self.tools.append(tool)

    def add_instruction(self, instruction):
        if len(instruction) == 0:
            return False

        instruction = replace_choosing_sections(instruction)
        instruction += "."

        self.instructions.append(instruction)
        return True

    def create(self):
        available_materials = list(map(lambda material: material.copy(), self.materials))

        instruction_count_target = random.randint(5, 10)
        tries_left = 100
        while (len(self.instructions) < instruction_count_target) and (tries_left > 0):
            tool = random.choice(self.tools)
            instruction = tool.execute_random_action(available_materials)
            if not self.add_instruction(instruction):
                tries_left -= 1

        for tool in self.tools:
            if tool.is_filled():
                self.add_instruction(tool.execute_random_generating_filled_action(available_materials))

        if len(available_materials) > 0:
            instruction = "Drop " + \
                          concat_list(available_materials, lambda material: material.get_label_full()) + \
                          " into a pile on the floor"
            self.add_instruction(instruction)
            self.add_instruction("Wait until they magically transform into a " + self.end_product)
        else:
            self.add_instruction("Wait a bit until a " + self.end_product + " suddenly appears")

    def print(self):
        print("How to make a " + self.end_product + " in " + str(len(self.instructions)) + " easy steps:")
        print()

        print("Materials:")
        for material in self.materials:
            print(" - " + material.get_label_full())
        print()

        print("Tools:")
        for tool in self.tools:
            if tool.has_label():
                print(" - " + tool.get_label())
        print()

        print("Instructions:")
        index = 1
        for instruction in self.instructions:
            print(str(index) + ". " + instruction)
            index += 1

        print()


class Material(object):
    def __init__(self, name, amount, quantity_type):
        self.name = ""
        self.name_plural = ""
        self.rename(name)
        self.amount = amount
        self.quantity_type = quantity_type

    def get_label_full(self):
        return self.quantity_type.get_material_label(self, self.amount)

    def get_label_short(self):
        return self.name

    def equals(self, other_material):
        return self.name == other_material.name

    def rename(self, name):
        self.name = name
        self.name_plural = pluralize(name)

    def copy(self):
        return Material(self.name, self.amount, self.quantity_type)


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
        value_min = 1
        value_max = 10

        for i in range(5):
            if random.random() < 0.1:
                value_max *= random.randint(2, 5)

        if self.integer_only:
            return random.randint(value_min, value_max)

        return round(random.uniform(value_min, value_max) * 100) / 100


class Tool(object):
    def __init__(self, tool_type):
        self.tool_type = tool_type
        if tool_type.name_list:
            self.name = random.choice(tool_type.name_list)
        else:
            self.name = ""

        self.filling_materials = []

    def has_label(self):
        return len(self.name) > 0

    def get_label(self):
        return self.name

    def equals(self, other_tool):
        return self.name == other_tool.name

    def execute_random_action(self, available_materials):
        result = ""
        materials_available = len(available_materials) > 0

        tries_left = 20

        while (len(result) == 0) and (tries_left > 0):
            random_value = random.random() * ToolType.CHANCE_TOTAL

            if random_value <= ToolType.CHANCE_SIMPLE_ACTION:
                if len(self.tool_type.simple_actions) > 0:
                    result = self.call_simple_action(*random.choice(self.tool_type.simple_actions))
                    continue

            random_value -= ToolType.CHANCE_SIMPLE_ACTION

            if random_value <= ToolType.CHANCE_CONSUMING_ACTION:
                if (len(self.tool_type.simple_actions) > 0) and materials_available:
                    result = self.call_material_consuming_action(available_materials, *random.choice(self.tool_type.consuming_actions))
                    continue

            random_value -= ToolType.CHANCE_CONSUMING_ACTION

            if random_value <= ToolType.CHANCE_TRANSFORMING_ACTION:
                if (len(self.tool_type.transforming_actions)) > 0 and materials_available:
                    result = self.call_material_transforming_action(available_materials, *random.choice(self.tool_type.transforming_actions))
                    continue

            random_value -= ToolType.CHANCE_TRANSFORMING_ACTION

            if random_value <= ToolType.CHANCE_GENERATING_ACTION:
                actions = self.tool_type.generating_actions_all if self.is_filled() else self.tool_type.generating_actions_possible_when_unfilled
                if len(actions) > 0:
                    result = self.call_generating_action(available_materials, *random.choice(actions))
                    continue

            # random_value -= ToolType.CHANCE_GENERATING_ACTION

            tries_left -= 1

        return result

    def execute_random_generating_filled_action(self, available_materials):
        if not self.is_filled() or len(self.tool_type.generating_actions_only_when_filled) == 0:
            return ""

        return self.call_generating_action(available_materials, *random.choice(self.tool_type.generating_actions_only_when_filled))

    def call_simple_action(self, instruction):
        return self.default_replace(instruction)

    def call_material_consuming_action(self, available_materials, instruction):
        material = take_random_material(available_materials)
        self.filling_materials.append(material)
        return self.default_replace(instruction)\
            .replace("{material}", material.get_label_full())

    def call_material_transforming_action(self, available_materials, instruction, result):
        material = take_random_material(available_materials)
        original_material_label = material.get_label_full()

        material.rename(result.replace("{material}", material.name))
        available_materials.append(material)

        return self.default_replace(instruction)\
            .replace("{material}", original_material_label)

    def call_generating_action(self, available_materials, instruction, result, possible_quantity_types, only_when_filled):
        material_name = self.default_replace(result)
        quantity_type = random.choice(possible_quantity_types)
        result_material = Material(material_name, quantity_type.random_amount(), quantity_type)
        available_materials.append(result_material)

        result = self.default_replace(instruction).replace("{result}", result_material.get_label_full())

        if only_when_filled:
            self.filling_materials.clear()

        return result

    def default_replace(self, string):
        return string.replace("{tool}", self.name) \
                     .replace("{contents}", concat_list(self.filling_materials, lambda material: material.get_label_short()))

    def is_filled(self):
        return len(self.filling_materials) > 0


class ToolType(object):
    CHANCE_SIMPLE_ACTION = 1
    CHANCE_CONSUMING_ACTION = 1
    CHANCE_TRANSFORMING_ACTION = 1
    CHANCE_GENERATING_ACTION = 1
    CHANCE_TOTAL = CHANCE_SIMPLE_ACTION + CHANCE_CONSUMING_ACTION + CHANCE_TRANSFORMING_ACTION + CHANCE_GENERATING_ACTION

    def __init__(self, name_list=False):
        self.name_list = name_list
        self.simple_actions = []
        self.consuming_actions = []
        self.transforming_actions = []
        self.generating_actions_possible_when_unfilled = []
        self.generating_actions_only_when_filled = []
        self.generating_actions_all = []

    def add_simple_action(self, instruction):
        self.simple_actions.append((instruction,))

    def add_material_consuming_action(self, instruction):
        self.consuming_actions.append((instruction,))

    def add_material_transforming_action(self, instruction, result):
        self.transforming_actions.append((instruction, result))

    def add_generating_action(self, instruction, result, possible_quantity_types, only_when_filled):
        data = (instruction, result, possible_quantity_types, only_when_filled)

        if only_when_filled:
            self.generating_actions_only_when_filled.append(data)
        else:
            self.generating_actions_possible_when_unfilled.append(data)

        self.generating_actions_all.append(data)


def take_random_material(available_materials):
    index = random.randint(0, len(available_materials) - 1)
    material = available_materials[index]
    del available_materials[index]
    return material


def replace_choosing_sections(string):
    (index_start, index_end) = find_choosing_section_from_to(string)
    while (index_start != -1) and (index_end != -1):
        start_string = string[:index_start]
        end_string = string[(index_end+1):]

        option_string = string[(index_start+1):index_end]
        option_list = split_ignore_choosing_sections(option_string)
        option = random.choice(option_list)

        # print("> " + start_string)
        # print("~ " + str(option_list))
        # print("< " + end_string)

        string = start_string + option + end_string

        (index_start, index_end) = find_choosing_section_from_to(string)

    return string


def find_choosing_section_from_to(string):
    index_start = string.find("[")
    index_end = -1
    counter = 1
    for index in range(index_start + 1, len(string)):
        char = string[index]
        if char == '[':
            counter += 1
        elif char == ']':
            counter -= 1
            if counter == 0:
                index_end = index
                break

    return index_start, index_end


def split_ignore_choosing_sections(string):
    result = []
    start = 0
    counter = 0
    for index in range(len(string)):
        char = string[index]
        if char == '[':
            counter += 1
        elif char == ']':
            counter -= 1
        elif char == '|' and counter == 0:
            result.append(string[start:index])
            start = index+1

    result.append(string[start:])

    return result


def pluralize(word):
    if word.endswith("s"):
        return word

    return word + "s"


def choose_and_remove(elements):
    index = random.randint(0, len(elements) - 1)
    item = elements[index]
    del elements[index]
    return item


def concat_list(elements, transform_function=lambda x: x):
    result = ""
    count = len(elements)
    for index in range(count):
        if index > 0:
            if index == count - 1:
                result += " and "
            else:
                result += ", "

        result += transform_function(elements[index])
    return result
