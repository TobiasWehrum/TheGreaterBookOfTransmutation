import random
import tools
from pylatex import Document, Section, Subsection, Table, Math, TikZ, Axis, \
    Plot, Figure, Package, Itemize, Enumerate
from pylatex.command import Command
from pylatex.utils import italic, bold
import re


class Recipe(object):
    def __init__(self, end_product, ending_tools):
        super(Recipe, self).__init__()

        self.end_product = end_product
        self.end_product_indefinite_article = tools.get_indefinite_article(self.end_product) + " "

        if tools.is_uncountable_noun(self.end_product):
            self.end_product_indefinite_article = ""
        elif not tools.DEBUG_SKIP_WORD_ANALYSIS and not tools.has_word_type(self.end_product, [tools.WORD_TYPE_NOUN]):
            word_type = tools.find_most_common_word_type(self.end_product)
            if word_type == tools.WORD_TYPE_VERB:
                self.end_product = "something that can " + self.end_product
                self.end_product_indefinite_article = ""
            elif word_type == tools.WORD_TYPE_ADJECTIVE:
                self.end_product = "something " + self.end_product
                self.end_product_indefinite_article = ""

        self.ending_tools = ending_tools
        self.materials = []
        self.tools = []
        self.instructions = []
        self.available_materials = []
        self.ending_tool_tools = []

    def add_material(self, material):
        self.materials.append(material)

    def add_tool(self, tool):
        self.tools.append(tool)

    def add_instruction(self, instruction):
        instruction = replace_choosing_sections(instruction)
        if instruction[-1].isalpha():
            instruction += "."

        self.instructions.append(instruction)
        return True

    def has_materials_available(self):
        return len(self.available_materials) > 0

    def available_materials_count(self):
        return len(self.available_materials)

    def take_random_material(self):
        index = random.randint(0, len(self.available_materials) - 1)
        material = self.available_materials[index]
        del self.available_materials[index]
        return material

    def choose_random_material(self):
        return random.choice(self.available_materials)

    def finish(self):
        self.available_materials = list(map(lambda material: material.copy(), self.materials))

        instruction_count_target = random.randint(random.randint(2, 5), 10)
        tries_left = 100
        while (len(self.instructions) < instruction_count_target) and (tries_left > 0):
            chosen_tool = tools.random_weighted_choice(self.tools, lambda t: t.current_chance_sum())
            if chosen_tool.execute_random_action(self):
                for tool in self.tools:
                    tool.advance_cooldowns()
            else:
                tries_left -= 1

        for tool in self.tools:
            if tool.is_filled():
                tool.execute_random_generating_filled_action(self)

        """
        if self.has_materials_available():
            instruction = "Drop " + \
                          tools.concat_list(self.available_materials, lambda material: material.get_label_full()) + \
                          " into a pile on the floor"
            self.add_instruction(instruction)
            self.add_instruction("Wait until they magically transform into " + self.end_product_with_indefinite_article)
        else:
            self.add_instruction("Wait a bit until " + self.end_product_with_indefinite_article + " suddenly appears")
        """

        self.tools = [tool for tool in self.tools if tool.used]

        has_materials_available = self.has_materials_available()
        while True:
            ending_tool = random.choice(self.ending_tools)
            if ending_tool.uses_materials == has_materials_available:
                self.ending_tool_tools = ending_tool.get_concrete_tools()
                ending_tool.execute(self, self.ending_tool_tools)
                break

    def print(self):
        print("How to make " + self.end_product_indefinite_article + "e{{" + self.end_product + "}}e in " + str(len(self.instructions)) + " easy steps:")
        print()

        print("Materials:")
        for material in self.materials:
            print(" - " + material.get_label_full())
        print()

        print("Tools:")
        tools_added = False
        for tool in self.tools:
            if tool.has_label():
                print(" - " + tool.get_label().capitalize())
                tools_added = True
        for tool in self.ending_tool_tools:
            print(" - " + tool.capitalize())
            tools_added = True
        if not tools_added:
            print(" - None")
        print()

        print("Instructions:")
        index = 1
        for instruction in self.instructions:
            print(str(index) + ". " + instruction)
            index += 1

        print()

    def count_words(self):
        words = count_words(self.end_product_indefinite_article + self.end_product)
        words += count_words("How to make " + self.end_product_indefinite_article + self.end_product + " in " + str(len(self.instructions)) + " easy steps")
        words += count_words("Materials")
        for material in self.materials:
            words += count_words(material.get_label_full())

        words += count_words("Tools")
        tools_added = False
        for tool in self.tools:
            if tool.has_label():
                words += count_words(tool.get_label())
                tools_added = True
        for tool in self.ending_tool_tools:
            words += count_words(tool)
            tools_added = True
        if not tools_added:
            words += count_words("None")

        words += count_words("Instructions")
        for instruction in self.instructions:
            words += count_words(instruction.replace("m{{", "").replace("t{{", "").replace("e{{", "").replace("}}m", "").replace("}}t", "").replace("}}e", ""))

        return words

    def print_to_doc(self, doc):
        with doc.create(Section((self.end_product_indefinite_article + self.end_product).capitalize())):
            doc.append("How to make " + self.end_product_indefinite_article + "\\textbf{" + self.end_product + "} in " + str(len(self.instructions)) + " easy steps:\n")

            with doc.create(Subsection("Materials")):
                with doc.create(Itemize()) as itemize:
                    for material in self.materials:
                        itemize.add_item(material.get_label_full().replace("&", "\\&"))

            with doc.create(Subsection("Tools")):
                with doc.create(Itemize()) as itemize:
                    tools_added = False
                    for tool in self.tools:
                        if tool.has_label():
                            itemize.add_item(tool.get_label().capitalize())
                            tools_added = True
                    for tool in self.ending_tool_tools:
                        itemize.add_item(tool.capitalize())
                        tools_added = True

                    if not tools_added:
                        itemize.add_item("None")

            with doc.create(Subsection("Instructions")):
                with doc.create(Enumerate()) as enum:
                    for instruction in self.instructions:
                        instruction = instruction.replace("e{{", "\\textbf{")
                        instruction = instruction.replace("}}e", "}")
                        instruction = instruction.replace("m{{", "\\textbf{")
                        instruction = instruction.replace("}}m", "}")
                        instruction = instruction.replace("t{{", "")  # \\textit{
                        instruction = instruction.replace("}}t", "")
                        instruction = instruction.replace("&", "\\&")
                        enum.add_item(instruction)
                        """
                        enum.add_item("")
                        start = instruction.find("{{")
                        while start != -1:
                            end = instruction.find("}}")
                            if start > 1:
                                enum.append(instruction[:start-1])

                            type = instruction[start-1:start]
                            item = instruction[start+2:end]
                            if type == "m":
                                enum.append(italic(item))
                            else:
                                enum.append(bold(item))

                            instruction = instruction[end+3:]
                            start = instruction.find("{{")

                        if len(instruction) > 0:
                            enum.append(instruction)
                        """

            doc.append(Command("newpage"))


class Material(object):
    def __init__(self, name, amount, quantity_type, adjectives = 0):
        super(Material, self).__init__()
        self.name = ""
        self.name_plural = ""
        self.rename(name)
        self.amount = amount
        self.quantity_type = quantity_type

        if adjectives == 0:
            adjectives = []
        self.adjectives = adjectives

    def get_label_full(self):
        return self.quantity_type.get_material_label(self, self.amount)

    def has_adjectives(self):
        return len(self.adjectives) > 0

    def get_adjectives_label(self):
        return tools.concat_list(self.adjectives)

    def get_label_short(self, plural=False, include_adjectives=True):
        result = ""
        if include_adjectives and self.has_adjectives():
            result += self.get_adjectives_label() + " "
        result += self.name if not plural else self.name_plural
        return result

    def equals(self, other_material):
        return self.name == other_material.name

    def rename(self, name):
        self.name = name
        self.name_plural = tools.pluralize(name)

    def them_or_it(self):
        return "it" if self.amount == 1 else "them"

    def copy(self):
        return Material(self.name, self.amount, self.quantity_type, list(self.adjectives))


class QuantityType(object):
    def __init__(self, singular_format, pluralized_format, integer_only):
        super(QuantityType, self).__init__()
        self.singular_format = singular_format
        self.pluralized_format = pluralized_format
        self.integer_only = integer_only

    def get_material_label(self, material, amount):
        adjectives = ""
        if material.has_adjectives():
            adjectives += " " + material.get_adjectives_label()

        return (self.singular_format if amount == 1 else self.pluralized_format)\
            .replace("{amount}", str(amount))\
            .replace(" {adjectives}", adjectives)\
            .replace("{material}", material.get_label_short(False, False))\
            .replace("{material_plural}", material.get_label_short(True, False))

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
        super(Tool, self).__init__()
        self.tool_type = tool_type
        if tool_type.name_list:
            self.name = replace_choosing_sections(random.choice(tool_type.name_list))
        else:
            self.name = ""

        self.filling_materials = []
        self.actions = list(map(lambda action: action.copy(), tool_type.actions))
        self.generating_actions_only_when_filled = [action for action in self.actions if isinstance(action, ActionGenerating) and action.only_when_filled]
        self.used = False
        self.values = tool_type.values.copy()

    def has_label(self):
        return len(self.name) > 0

    def get_label(self):
        return self.name

    def equals(self, other_tool):
        return self.name == other_tool.name

    def current_chance_sum(self):
        return sum(map(lambda action: action.current_chance(), self.actions))

    def execute_random_action(self, recipe):
        tries_left = 20

        while tries_left > 0:
            action = tools.random_weighted_choice(self.actions, lambda a: a.current_chance())
            if action.execute(self, recipe):
                self.used = True
                return True

            tries_left -= 1

        return False

    def execute_random_generating_filled_action(self, recipe):
        if not self.is_filled() or len(self.generating_actions_only_when_filled) == 0:
            return False

        action = random.choice(self.generating_actions_only_when_filled)
        return action.execute(self, recipe)

    def advance_cooldowns(self):
        for action in self.actions:
            action.cooldown_left -= 1

    def default_replace(self, string):
        return string.replace("{tool}", "t{{" + self.name + "}}t") \
                     .replace("{contents}", tools.concat_list(self.filling_materials, lambda material: material.get_label_short()))

    def is_filled(self):
        return len(self.filling_materials) > 0


class ToolType(object):
    def __init__(self, name_list=False, initial_values=False):
        self.name_list = name_list
        self.actions = []
        self.values = initial_values if initial_values else []
        self.chance_value = 1

    def add(self, action):
        self.actions.append(action)
        return self

    def chance(self, value):
        self.chance_value = value
        return self


class Action(object):
    def __init__(self):
        super(Action, self).__init__()
        self.cooldown_value = 2
        self.cooldown_left = 0
        self.chance_value = 1
        self.condition_delegate = 0
        self.post_execution_sets = []

    @staticmethod
    def copy_into(source, copied_action):
        copied_action.cooldown_value = source.cooldown_value
        copied_action.chance_value = source.chance_value
        copied_action.condition_delegate = source.condition_delegate
        copied_action.post_execution_sets = source.post_execution_sets

    def cooldown(self, value):
        self.cooldown_value = value
        return self

    def chance(self, value):
        self.chance_value = value
        return self

    def condition(self, delegate):
        self.condition_delegate = delegate
        return self

    def afterwards(self, key, value):
        self.post_execution_sets.append((key, value))
        return self

    def current_chance(self):
        return self.chance_value

    def execute(self, tool, recipe):
        if self.cooldown_left > 0:
            return False

        if self.condition_delegate != 0 and not self.condition_delegate(tool, recipe):
            return False

        successful = self.execute_internal(tool, recipe)
        if successful:
            self.cooldown_left = self.cooldown_value + 1

        for post_execution_set in self.post_execution_sets:
            tool.values[post_execution_set[0]] = post_execution_set[1]

        return successful


class ActionSimple(Action):
    def __init__(self, instruction, uses_material = False):
        super(ActionSimple, self).__init__()
        self.instruction = instruction
        self.uses_material = uses_material

    def copy(self):
        copied_action = ActionSimple(self.instruction, self.uses_material)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        result = tool.default_replace(self.instruction)

        if self.uses_material:
            if not recipe.has_materials_available():
                return False

            material = recipe.choose_random_material()
            result = result.replace("{material}", "m{{" + material.get_label_full() + "}}m") \
                           .replace("{material_it}", material.them_or_it())

        recipe.add_instruction(result)
        return True


class ActionConsuming(Action):
    def __init__(self, instruction, destroying = False):
        super(ActionConsuming, self).__init__()
        self.instruction = instruction
        self.destroying = destroying

    def copy(self):
        copied_action = ActionConsuming(self.instruction, self.destroying)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if not recipe.has_materials_available():
            return False

        material = recipe.take_random_material()

        if not self.destroying:
            tool.filling_materials.append(material)

        result = tool.default_replace(self.instruction) \
            .replace("{material}", "m{{" + material.get_label_full() + "}}m") \
            .replace("{material_it}", material.them_or_it())

        recipe.add_instruction(result)

        return True


class ActionTransforming(Action):
    def __init__(self, instruction, result):
        super(ActionTransforming, self).__init__()
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
        original_material_then_or_it = material.them_or_it()

        material.rename(self.result.replace("{material}", material.name))
        recipe.available_materials.append(material)

        result = tool.default_replace(self.instruction) \
            .replace("{material}", "m{{" + original_material_label + "}}m") \
            .replace("{material_it}", original_material_then_or_it)

        recipe.add_instruction(result)

        return True


class ActionAdjectivize(Action):
    def __init__(self, instruction, adjectives):
        super(ActionAdjectivize, self).__init__()
        self.instruction = instruction
        self.adjectives = adjectives

    def copy(self):
        copied_action = ActionAdjectivize(self.instruction, self.adjectives)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if not recipe.has_materials_available():
            return False

        material = recipe.choose_random_material()
        original_material_label = material.get_label_full()
        original_material_then_or_it = material.them_or_it()

        my_adjectives_count = len(self.adjectives)
        current_adjective_index = -1
        existing_index = -1
        for my_adjective_index in range(my_adjectives_count):
            for material_adjective_index in range(len(material.adjectives)):
                if self.adjectives[my_adjective_index] == material.adjectives[material_adjective_index]:
                    existing_index = material_adjective_index
                    current_adjective_index = my_adjective_index
                    break

        if current_adjective_index == my_adjectives_count - 1:
            return False

        new_adjective = self.adjectives[current_adjective_index + 1]

        if existing_index >= 0:
            material.adjectives[existing_index] = new_adjective
        else:
            material.adjectives.append(new_adjective)

        result = tool.default_replace(self.instruction) \
            .replace("{material}", "m{{" + original_material_label + "}}m") \
            .replace("{material_it}", original_material_then_or_it) \
            .replace("{result}", "m{{" + material.get_label_full() + "}}m")

        recipe.add_instruction(result)

        return True


class ActionGenerating(Action):
    def __init__(self, instruction, result, possible_quantity_types, only_when_filled):
        super(ActionGenerating, self).__init__()
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

        result = tool.default_replace(self.instruction).replace("{result}", "m{{" + result_material.get_label_full() + "}}m")

        if self.only_when_filled:
            tool.filling_materials.clear()

        recipe.add_instruction(result)

        return True


class ActionConsumeEverything(Action):
    def __init__(self, instruction, destroying=False):
        super(ActionConsumeEverything, self).__init__()
        self.instruction = instruction
        self.destroying = destroying

    def copy(self):
        copied_action = ActionConsumeEverything(self.instruction, self.destroying)
        Action.copy_into(self, copied_action)
        return copied_action

    def execute_internal(self, tool, recipe):
        if not recipe.has_materials_available():
            return False

        thrown_away_materials = []
        while recipe.has_materials_available():
            material = recipe.take_random_material()

            if not self.destroying:
                tool.filling_materials.append(material)

            thrown_away_materials.append(material)

        result = tool.default_replace(self.instruction) \
                     .replace("{materials}", tools.concat_list(thrown_away_materials, lambda m: "m{{" + m.get_label_full() + "}}m"))

        recipe.add_instruction(result)

        return True


class EndingTool(object):
    def __init__(self, uses_materials, tools):
        super(EndingTool, self).__init__()
        self.uses_materials = uses_materials
        self.tools = tools

    def get_concrete_tools(self):
        return list(map(lambda tool: replace_choosing_sections(tool), self.tools))

    def execute(self, recipe, concrete_tools):
        pass

    @staticmethod
    def default_replace(line, recipe, concrete_tools, replacement_tuples):
        line = replace_choosing_sections(line)

        line = line.replace("{materials}", tools.concat_list(recipe.available_materials, lambda material: "m{{" + material.get_label_full() + "}}m")) \
                   .replace("{product}", "e{{" + recipe.end_product + "}}e") \
                   .replace("{aproduct}", recipe.end_product_indefinite_article + "e{{" + recipe.end_product + "}}e")

        index = 1
        for tool in concrete_tools:
            line = line.replace("{tool" + str(index) + "}", tool)
            index += 1

        for replacement_tuple in replacement_tuples:
            line = line.replace(replacement_tuple[0], replacement_tuple[1])

        return line


class EndingToolDefault(EndingTool):
    def __init__(self, uses_materials, tools, lines):
        EndingTool.__init__(self, uses_materials, tools)
        self.lines = lines
        self.replacement_tuples_by_condition = []
        self.replacement_tuples_delegates = []

    def add_replacement_tuple_by_condition(self, replace_string, replace_with, condition):
        self.replacement_tuples_by_condition.append((replace_string, replace_with, condition))
        return self

    def add_replacement_tuple_delegate(self, delegate):
        self.replacement_tuples_delegates.append(delegate)
        return self

    def execute(self, recipe, concrete_tools):
        replacement_tuples = []
        for replacement_tuple_by_condition in self.replacement_tuples_by_condition:
            condition = replacement_tuple_by_condition[2]
            if condition(recipe):
                replacement_tuples.append((replacement_tuple_by_condition[0], replacement_tuple_by_condition[1]))

        for replacement_tuple_delegate in self.replacement_tuples_delegates:
            replacement_tuple_delegate(recipe, concrete_tools, replacement_tuples)

        for line in self.lines:
            line = self.default_replace(line, recipe, concrete_tools, replacement_tuples)  # First wave
            line = self.default_replace(line, recipe, concrete_tools, replacement_tuples)  # Second wave
            recipe.add_instruction(line)


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


def create_spell(markov):
    result = ""
    for i in range(random.randint(1, random.randint(1, 5))):
        if len(result) > 0:
            result += " "

        word_count = random.randint(1, random.randint(1, 8))
        comma_position = -1
        if word_count >= 4 and random.random() > 0.5:
            comma_position = random.randint(2, word_count - 2)
        result += create_sentence(markov, word_count, comma_position, ["!"], 12)

    return result


def create_sentence(markov, word_count, comma_position, sentence_end, max_word_length):
    result = ""
    for i in range(word_count):
        if len(result) > 0:
            result += " "

        word = create_word(markov)
        while len(word) > max_word_length:
            word = create_word(markov)

        result += word
        if i == comma_position:
            result += ","

    result = result.capitalize()

    result += random.choice(sentence_end)
    return result


def create_word(markov):
    return "".join(markov.generate())


def count_words(str):
    # print(str)
    # print(len(re.findall(r'\b[\w.]+\b', str)))
    return len(re.findall(r'\b[\w.]+\b', str))