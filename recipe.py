import random
import inflect

p = inflect.engine()


class Recipe(object):
    def __init__(self, end_product):
        self.end_product = end_product
        self.materials = []
        self.tools = []
        self.instructions = []
        self.available_materials = []

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

    def has_materials_available(self):
        return len(self.available_materials) > 0

    def take_random_material(self):
        index = random.randint(0, len(self.available_materials) - 1)
        material = self.available_materials[index]
        del self.available_materials[index]
        return material

    def finish(self):
        self.available_materials = list(map(lambda material: material.copy(), self.materials))

        instruction_count_target = random.randint(5, 10)
        tries_left = 100
        while (len(self.instructions) < instruction_count_target) and (tries_left > 0):
            tool = random.choice(self.tools)
            if tool.execute_random_action(self):
                for t in self.tools:
                    t.advance_cooldowns()
            else:
                tries_left -= 1

        for tool in self.tools:
            if tool.is_filled():
                tool.execute_random_generating_filled_action(self)

        if self.has_materials_available():
            instruction = "Drop " + \
                          concat_list(self.available_materials, lambda material: material.get_label_full()) + \
                          " into a pile on the floor"
            self.add_instruction(instruction)
            self.add_instruction("Wait until they magically transform into a " + self.end_product)
        else:
            self.add_instruction("Wait a bit until a " + self.end_product + " suddenly appears")

        self.tools = [tool for tool in self.tools if tool.used]

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
        self.adjectives = []

    def get_label_full(self):
        return self.quantity_type.get_material_label(self, self.amount)

    def get_label_short(self, plural=False):
        result = ""
        result += self.name if not plural else self.name_plural
        return result

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
            .replace("{material}", material.get_label_short(False))\
            .replace("{material_plural}", material.get_label_short(True))

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
        self.actions = list(map(lambda action: action.copy(), tool_type.actions))
        self.generating_actions_only_when_filled = [action for action in self.actions if action is ActionGenerating and action.only_when_filled]
        self.used = False

    def has_label(self):
        return len(self.name) > 0

    def get_label(self):
        return self.name

    def equals(self, other_tool):
        return self.name == other_tool.name

    def execute_random_action(self, recipe):
        tries_left = 20

        while tries_left > 0:
            action = random.choice(self.actions)
            if action.execute(self, recipe):
                self.used = True
                return True

            tries_left -= 1

        return False

    def execute_random_generating_filled_action(self, available_materials):
        if not self.is_filled() or len(self.generating_actions_only_when_filled) == 0:
            return False

        action = random.choice(self.generating_actions_only_when_filled)
        return action.execute()

    def advance_cooldowns(self):
        for action in self.actions:
            action.cooldown_left -= 1

    def default_replace(self, string):
        return string.replace("{tool}", self.name) \
                     .replace("{contents}", concat_list(self.filling_materials, lambda material: material.get_label_short()))

    def is_filled(self):
        return len(self.filling_materials) > 0


class ToolType(object):
    def __init__(self, name_list=False):
        self.name_list = name_list
        self.actions = []

    def add(self, action):
        self.actions.append(action)


class Action(object):
    def __init__(self):
        self.cooldown_value = 0
        self.cooldown_left = 0

    @staticmethod
    def copy_into(source, copied_action):
        copied_action.cooldown_value = source.cooldown_value

    def cooldown(self, value):
        self.cooldown_value = value
        return self

    def execute(self, tool, recipe):
        if self.cooldown_left > 0:
            return False

        successful = self.execute_internal(tool, recipe)
        if successful:
            self.cooldown_left = self.cooldown_value + 1

        return successful


class ActionSimple(Action):
    def __init__(self, instruction):
        Action.__init__(self)
        self.instruction = instruction

    def copy(self):
        copied_action = ActionSimple(self.instruction)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        result = tool.default_replace(self.instruction)
        recipe.add_instruction(result)
        return True


class ActionConsuming(Action):
    def __init__(self, instruction):
        Action.__init__(self)
        self.instruction = instruction

    def copy(self):
        copied_action = ActionConsuming(self.instruction)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if not recipe.has_materials_available():
            return False

        material = recipe.take_random_material()
        tool.filling_materials.append(material)

        result = tool.default_replace(self.instruction)\
            .replace("{material}", material.get_label_full())

        recipe.add_instruction(result)

        return True


class ActionTransforming(Action):
    def __init__(self, instruction, result):
        Action.__init__(self)
        self.instruction = instruction
        self.result = result

    def copy(self):
        copied_action = ActionTransforming(self.instruction, self.result)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if not recipe.has_materials_available():
            return False

        material = recipe.take_random_material()
        original_material_label = material.get_label_full()

        material.rename(self.result.replace("{material}", material.name))
        recipe.available_materials.append(material)

        result = tool.default_replace(self.instruction)\
            .replace("{material}", original_material_label)

        recipe.add_instruction(result)

        return True


class ActionGenerating(Action):
    def __init__(self, instruction, result, possible_quantity_types, only_when_filled):
        Action.__init__(self)
        self.instruction = instruction
        self.result = result
        self.possible_quantity_types = possible_quantity_types
        self.only_when_filled = only_when_filled

    def copy(self):
        copied_action = ActionGenerating(self.instruction, self.result, self.possible_quantity_types, self.only_when_filled)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if self.only_when_filled and not tool.is_filled():
            return False

        material_name = tool.default_replace(self.result)
        quantity_type = random.choice(self.possible_quantity_types)
        result_material = Material(material_name, quantity_type.random_amount(), quantity_type)
        recipe.available_materials.append(result_material)

        result = tool.default_replace(self.instruction).replace("{result}", result_material.get_label_full())

        if self.only_when_filled:
            tool.filling_materials.clear()

        recipe.add_instruction(result)

        return True


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
    return p.plural(word)
    # if word.endswith("s"):
    #    return word
    # return word + "s"


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

