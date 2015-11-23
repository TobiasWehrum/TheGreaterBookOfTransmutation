import random
import data
import recipe
from recipe import Recipe
from recipe import Material
from recipe import QuantityType
from recipe import Tool
from recipe import ToolType
from recipe import ActionSimple
from recipe import ActionConsuming
from recipe import ActionGenerating
from recipe import ActionTransforming
from recipe import ActionAdjectivize
from recipe import EndingToolDefault
from generator import Markov
import tools

RELEASE = False

DEBUG_REDUCE_LATIN_WORD_LIST = True and not RELEASE
data.DEBUG_REDUCE_WORD_LIST = True and not RELEASE
tools.DEBUG_SKIP_WORLD_ANALYSIS = True and not RELEASE
tools.DEBUG_OUTPUT = True
UPDATE_NLTK_CORPI = False


def main():
    if UPDATE_NLTK_CORPI:
        tools.download_corpi()

    words = data.load_latin_words()
    latin_markov = Markov(3)
    if not DEBUG_REDUCE_LATIN_WORD_LIST:
        for word in words:
            latin_markov.add(word.lower())
    else:
        for word in random.sample(words, 100):
            latin_markov.add(word.lower())

    # for i in range(10): print(recipe.create_spell(latin_markov))
    # return

    word_associations = data.load_usf_free_association_files()

    quantity_type_countable = QuantityType("{amount} {material}", "{amount} {material_plural}", True)
    quantity_type_ounces = QuantityType("{amount} ounce of {material}", "{amount} ounces of {material}", False)
    quantity_type_spoonful = QuantityType("{amount} spoonful of {material}", "{amount} spoonful of {material}", False)
    quantity_type_idea = QuantityType("{amount} idea of {material}", "{amount} ideas of {material}", True)
    quantity_type_concept = QuantityType("{amount} clear concept of {material}", "{amount} clear concepts of {material}", True)
    quantity_type_notion = QuantityType("{amount} vague notion of {material}", "{amount} vague notions of {material}", True)
    quantity_type_idea_being = QuantityType("{amount} idea of being {material}", "{amount} ideas of being {material}", True)
    quantity_type_concept_being = QuantityType("{amount} clear concept of being {material}", "{amount} clear concepts of being {material}", True)
    quantity_type_notion_being = QuantityType("{amount} vague notion of being {material}", "{amount} vague notions of being {material}", True)

    quantity_type_noun = [quantity_type_countable, quantity_type_ounces, quantity_type_spoonful, quantity_type_idea, quantity_type_concept, quantity_type_notion]
    quantity_type_verb = [quantity_type_idea, quantity_type_concept, quantity_type_notion]
    quantity_type_adjective = [quantity_type_idea_being, quantity_type_concept_being, quantity_type_notion_being]
    quantity_types = {tools.WORD_TYPE_UNKNOWN: quantity_type_noun,
                      tools.WORD_TYPE_NOUN: quantity_type_noun,
                      tools.WORD_TYPE_ADJECTIVE: quantity_type_adjective,
                      tools.WORD_TYPE_VERB_PRESENT: quantity_type_verb}

    tool_type_vessel = ToolType(["cauldron", "container", "vessel"])  # , {"heated": False})
    tool_type_vessel.add(ActionConsuming("Put {material} into {tool}"))
    tool_type_vessel.add(ActionSimple("Stir {tool}").cooldown(2))
    tool_type_vessel.add(ActionSimple("Heat {tool}").cooldown(2))  # .condition(lambda tool, r: not tool.values["heated"]).afterwards("heated", True))
    tool_type_vessel.add(ActionSimple("Let {tool} cool down").cooldown(2))  # .condition(lambda tool, r: tool.values["heated"]).afterwards("heated", False))
    tool_type_vessel.add(ActionGenerating("Pour out the mixture from {tool} to get the {result}", "{tool} mixture \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True).cooldown(2))

    tool_type_smashing = ToolType(["hammer", "stone"])
    tool_type_smashing.add(ActionAdjectivize("Smash {material} with the {tool}", ["smashed", "pulverized"]).cooldown(2))
    tool_type_smashing.add(ActionAdjectivize("Crack {material} with the {tool}", ["cracked", "crushed"]).cooldown(2))

    tool_types = [tool_type_vessel, tool_type_smashing]

    tool_type_default = ToolType()
    # tool_type_default.add(ActionConsuming("Eat {material}").cooldown(2))
    tool_type_default.add(ActionSimple("Wait[| for [a[| very| rather] [short|long] time|[[a second|a minute|an hour|a day]|[2|3|4|5|6|7|8|9|10] [seconds|minutes|hours|days]]]]").cooldown(2))

    ending_tools = [EndingToolDefault(False, [], ["Wait a bit until {aproduct} suddenly appears"]),
                    EndingToolDefault(False, [], ["Wait until it rings on the door",
                                                  "Open the door. You will find {aproduct} just lying there",
                                                  "Don't ask how it got there. Take it. It's yours now"]),
                    EndingToolDefault(False, [], ["Buy {aproduct} on [Amazon|eBay]"]),
                    EndingToolDefault(False, [], ["Turn around. You will find that {aproduct} was there all along"]),
                    EndingToolDefault(False, [], ["Realise that you never really needed {aproduct}"]),
                    EndingToolDefault(True, [], ["Fold the {materials} together using advanced origami techniques",
                                                 "If you've done it correctly, it [should|might|could] result in {aproduct}"]),
                    EndingToolDefault(True, [], ["Dump the {materials} into a pile on the floor",
                                                 "Wait until they magically transform into {aproduct}"]),
                    EndingToolDefault(True, [], ["Use [glue|tape|nails|screws] to join the {materials} together into the [form|shape] of a [perfectly functional|passable|usable|beautiful] {product}"]),
                    EndingToolDefault(True, ["[ballpoint pen|charcoal pencil|graphite pencil|silverpoint pen|crayon|paintbrush|electric paint|fountain pen]"],
                                                ["Draw a magic circle on the floor using the {tool1}",
                                                 "{drawintoit}",
                                                 "[Chant|Intone|Whisper] the following spell: \"{spell}\"",
                                                 "[Suddendly|Slowly|Reluctantly], {aproduct} will appear inside the circle"])
                            .add_replacement_tuple_by_condition("{drawintoit}", "Draw a line into the circle and place {materials} on each end", lambda r: r.available_materials_count() == 2)
                            .add_replacement_tuple_by_condition("{drawintoit}", "Draw a triangle into the circle and place {materials} on each corner", lambda r: r.available_materials_count() == 3)
                            .add_replacement_tuple_by_condition("{drawintoit}", "Draw a [cross|square] into the circle and place {materials} on each corner", lambda r: r.available_materials_count() == 4)
                            .add_replacement_tuple_by_condition("{drawintoit}", "Draw a [pentagram|pentagon] into the circle and place {materials} on each corner", lambda r: r.available_materials_count() == 5)
                            .add_replacement_tuple_by_condition("{drawintoit}", "Draw a [hexagram|hexagon] into the circle and place {materials} on each corner", lambda r: r.available_materials_count() == 6)
                            .add_replacement_tuple_by_condition("{drawintoit}", "Place {materials} into the circle", lambda r: True)
                            .add_replacement_tuple_delegate(lambda r, concrete_tools, replacement_tuples: replacement_tuples.append(("{spell}", recipe.create_spell(latin_markov))))
                    ]

    for i in range(10):
        end_product = random.choice(list(word_associations.keys()))
        material_names = [t[0] for t in word_associations[end_product]]
        create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default, ending_tools)


def create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default, ending_tools):
    r = Recipe(end_product, ending_tools)

    for material_name in random.sample(material_names, min(4, len(material_names))):
        material_word_type = tools.find_most_common_word_type(material_name)

        # Unknown and length 12? Probably truncated, let's skip it.
        if material_word_type == tools.WORD_TYPE_UNKNOWN and len(material_name) == 12:
            continue

        if material_word_type in quantity_types:
            quantity_type = random.choice(quantity_types[material_word_type])
            amount = quantity_type.random_amount()

            r.add_material(Material(material_name, amount, quantity_type))

    for tool_type in random.sample(tool_types, min(2, len(tool_types))):
        tool = Tool(tool_type)
        # if not any(tool.equals(other_tool) for other_tool in r.tools):
        r.add_tool(tool)

    r.add_tool(Tool(tool_type_default))

    r.finish()

    print("=======================")
    print()
    r.print()


# Only run if we are the main program, not an import.
if __name__ == "__main__": main()
