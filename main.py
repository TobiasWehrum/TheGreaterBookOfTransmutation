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
from recipe import ActionConsumeEverything
from recipe import EndingToolDefault
from generator import Markov
import tools
import math
import time
import os
import traceback
from pylatex import Document, Section, Subsection, Table, Math, TikZ, Axis, \
    Plot, Figure, Package, Itemize, Enumerate
from pylatex.command import Command
from pylatex.utils import italic, bold

RELEASE = True

DEBUG_REDUCE_LATIN_WORD_LIST = True and not RELEASE
data.DEBUG_REDUCE_WORD_LIST = True and not RELEASE
tools.DEBUG_SKIP_WORD_ANALYSIS = True and not RELEASE
tools.DEBUG_OUTPUT = True
tools.DEBUG_OUTPUT_NOISY = True
UPDATE_NLTK_CORPI = False


def main():
    preparation_time = time.time()

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

    quantity_type_countable = QuantityType("{amount} {adjectives} {material}", "{amount} {adjectives} {material_plural}", True)
    quantity_type_ounces = QuantityType("{amount} ounce of {adjectives} {material}", "{amount} ounces of {adjectives} {material}", False)
    quantity_type_spoonful = QuantityType("{amount} spoonful of {adjectives} {material}", "{amount} spoonful of {adjectives} {material}", False)
    quantity_type_idea = QuantityType("{amount} {adjectives} idea of {material}", "{amount} {adjectives} ideas of {material}", True)
    quantity_type_concept = QuantityType("{amount} {adjectives} clear concept of {material}", "{amount} {adjectives} clear concepts of {material}", True)
    quantity_type_notion = QuantityType("{amount} {adjectives} vague notion of {material}", "{amount} {adjectives} vague notions of {material}", True)
    # quantity_type_idea_being = QuantityType("{amount} idea of being {material}", "{amount} ideas of being {material}", True)
    # quantity_type_concept_being = QuantityType("{amount} clear concept of being {material}", "{amount} clear concepts of being {material}", True)
    # quantity_type_notion_being = QuantityType("{amount} vague notion of being {material}", "{amount} vague notions of being {material}", True)

    quantity_type_noun = [quantity_type_countable, quantity_type_ounces, quantity_type_spoonful]
    quantity_type_verb = [quantity_type_idea, quantity_type_concept, quantity_type_notion]
    quantity_type_adjective = quantity_type_verb
    quantity_types = {tools.WORD_TYPE_UNKNOWN: quantity_type_noun,
                      tools.WORD_TYPE_NOUN: quantity_type_noun,
                      tools.WORD_TYPE_ADJECTIVE: quantity_type_adjective,
                      tools.WORD_TYPE_VERB: quantity_type_verb,
                      tools.WORD_TYPE_VERB_PRESENT: quantity_type_verb}

    joke_chance_tool = 0.1
    joke_chance_action = 0.013
    joke_cooldown = 1000

    tool_types = [ToolType(["cauldron", "container", "vessel"]) # , {"heated": False})
                  .add(ActionConsuming("Put {material} into the {tool}").cooldown(2))
                  .add(ActionSimple("Stir the {tool}"))
                  .add(ActionSimple("Heat the {tool}"))  # .condition(lambda tool, r: not tool.values["heated"]).afterwards("heated", True))
                  .add(ActionSimple("Let the {tool} cool down"))  # .condition(lambda tool, r: tool.values["heated"]).afterwards("heated", False))
                  .add(ActionGenerating("Pour out the mixture from the {tool} to get the {result}", "{tool} mixture \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True)),

                  ToolType(["hammer", "stone", "mortar"])
                  .add(ActionAdjectivize("Smash {material} with the {tool}", ["smashed", "pulverized"]))
                  .add(ActionAdjectivize("Crack {material} with the {tool}", ["cracked", "crushed"])),

                  ToolType(["saw"])
                  .add(ActionAdjectivize("Use the {tool} to slice {material} into bits", ["sliced", "fragmented"])),

                  ToolType(["purifier"])
                  .add(ActionAdjectivize("Purify {material} with the {tool}", ["purified"])),

                  ToolType(["bucket with [ice-cold |hot |ionised |clean |][water|liquid]"])
                  .add(ActionAdjectivize("Dip {material} into the {tool}", ["wet", "very wet", "extremely wet"])),

                  ToolType(["centrifuge"])
                  .add(ActionConsuming("Put {material} into the rotating {tool}").cooldown(0))
                  .add(ActionSimple("Speed up the {tool}").condition(lambda t, r: t.is_filled()))
                  .add(ActionGenerating("Stop the {tool} and retrieve the {result}", "centrifuged mixture \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True)),

                  ToolType(["bonfire", "fireplace"])
                  .add(ActionConsuming("Put {material} into the {tool}").cooldown(0))
                  .add(ActionAdjectivize("Hold {material} briefly into the {tool} to burn {material_it} a bit", ["slightly burned", "burned"]).cooldown(0))
                  .add(ActionSimple("Fan the flames of the {tool}"))
                  .add(ActionGenerating("Retrieve the {result} from the {tool}", "ashes of \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True)),

                  ToolType(["freezer"])
                  .add(ActionAdjectivize("Put {material} into the {tool} for a while", ["cooled", "frozen"])),

                  ToolType(["[pet|familiar] [cat|dog|unicorn|ape|mouse|chinchilla|hummingbird]"]).chance(joke_chance_tool)
                  .add(ActionConsuming("Feed {material} to your {tool}"))
                  .add(ActionSimple("Pet your {tool}"))
                  .add(ActionSimple("Let your {tool} sniff at {material}", True))
                  .add(ActionAdjectivize("Let your {tool} lick {material}", ["licked"]))
                  .add(ActionGenerating("Wait until your {tool} poops. Receive {result}", "a very dirty pile of \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True)),
                  ]

    tool_type_default = ToolType() \
        .add(ActionSimple("Wait[| for [a[| very| rather] [short|long] time|[[a second|a minute|an hour|a day]|[2|3|4|5|6|7|8|9|10] [seconds|minutes|hours|days]]]]")) \
        .add(ActionConsuming("Eat {material}").chance(joke_chance_action)) \
        .add(ActionConsuming("Throw {material} away").chance(joke_chance_action)) \
        .add(ActionConsumeEverything("Throw {materials} away").chance(joke_chance_action * 2)) \
        .add(ActionSimple("Pick up {material}. Turn {material_it} around. Look at {material_it} from every every side. [Nod satisfied|Shake your head [dissatisfied|with disgust]]. Put {material_it} back", True).cooldown(joke_cooldown).chance(joke_chance_action * 2)) \
        .add(ActionSimple("Grind a little bit of [unicorn horn|troll teeth|bat wings|antler of the extinct flying stag|hair from a president] to dust and add it. It's not strictly needed, but doesn't hurt I guess?").cooldown(joke_cooldown).chance(joke_chance_action / 2))

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
                    EndingToolDefault(True, ["[glue|tape|nails|screws]"], ["Use {tool1} to join the {materials} together into the [form|shape] of a [perfectly functional|passable|usable|beautiful] {product}"]),
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

    recipes = []

    preparation_time = time.time() - preparation_time

    starting_time = time.time()

    word_count = 0
    word_count_target = 50000
    end_products_left = list(word_associations.keys())
#    for i in range(10):
    while word_count < word_count_target and len(end_products_left) > 0:
        end_product = random.choice(end_products_left)
        end_products_left.remove(end_product)
        material_names = [t[0] for t in word_associations[end_product]]
        r = create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default, ending_tools)
        recipes.append(r)
        word_count += r.count_words()

        elapsed_time = (time.time() - starting_time) / 60
        percent_done = word_count/word_count_target

        total_elapsed_time = preparation_time + elapsed_time

        print("Word count: " + str(word_count) + "/" + str(word_count_target) + " (" + str(math.floor((percent_done)*100)) + "%)")
        print("Elapsed time: " + str(math.ceil(total_elapsed_time)) + "min, estimated remaining time: " + str(max(0, math.ceil(elapsed_time/percent_done - elapsed_time))) + "min")

    recipes = sorted(recipes, key=lambda a: a.end_product)

    create_pdf(recipes)


def create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default, ending_tools):
    """if not tools.has_word_type(end_product, [tools.WORD_TYPE_NOUN]):
        end_product_nounified = tools.nounify_first_result(end_product, "")
        if len(end_product_nounified) > 0 and end_product_nounified != end_product and end_product_nounified not in material_names:
            print("Nounified end product " + end_product + " => " + end_product_nounified)
            end_product = end_product_nounified
    """

    r = Recipe(end_product, ending_tools)

    for material_name in random.sample(material_names, min(4, len(material_names))):
        material_word_type = tools.find_most_common_word_type(material_name)

        # Unknown and length 12? Probably truncated, let's skip it.
        if material_word_type == tools.WORD_TYPE_UNKNOWN and len(material_name) == 12:
            continue

        if not tools.DEBUG_SKIP_WORD_ANALYSIS and material_word_type != tools.WORD_TYPE_NOUN and not tools.has_word_type(material_name, [tools.WORD_TYPE_NOUN]):
            material_name_nounified = tools.nounify_first_result(material_name, "")
            if len(material_name_nounified) > 0 and material_name_nounified != end_product and material_name_nounified not in material_names:
                print("Nounified material " + material_name + " => " + material_name_nounified)
                material_name = material_name_nounified
                material_word_type = tools.find_most_common_word_type(material_name)

        if material_word_type == tools.WORD_TYPE_ADJECTIVE:
            material_name = "being " + material_name

        if material_word_type in quantity_types:
            quantity_type = random.choice(quantity_types[material_word_type])
            amount = quantity_type.random_amount()

            r.add_material(Material(material_name, amount, quantity_type))

    tool_types = tool_types.copy()

    tool_count = random.randint(2, len(tool_types))

    # for tool_type in random.sample(tool_types, min(2, len(tool_types))):
    while len(r.tools) < tool_count:
        tool_type = tools.random_weighted_choice(tool_types, lambda t: t.chance_value)
        tool_types.remove(tool_type)

        tool = Tool(tool_type)
        # if not any(tool.equals(other_tool) for other_tool in r.tools):
        r.add_tool(tool)

    r.add_tool(Tool(tool_type_default))

    r.finish()

    print("=======================")
    print()
    r.print()

    return r


def create_pdf(recipes):
    doc = Document()
    doc.packages.append(Package("hyperref", options="hidelinks"))

    doc.append("\\begin{titlepage}\n"
               "\\centering\n"
               "{\\scshape\\Huge\\textbf The Greater Book of Transmutation \\par}\n"
               "\\vspace{1.5cm}\n"
               "{\\scshape\\large How to make almost anything in a few easy steps \\par}\n"
               "\\vspace{5.5cm}\n"
               "{\\large A Procedurally Generated DIY Book \\par}\n"
               "{\\large for the \href{https://github.com/dariusk/NaNoGenMo-2015}{NaNoGenMo 2015} \\par}\n"
               "\\vspace{0.5cm}\n"
               "{\\large by \\href{http://dragonlab.de}{Tobias Wehrum} \\par}\n"
               "\\vfill\n"
               "{\\scriptsize using data by: \\par}\n"
               "\\vspace{0.3cm}\n"
               "{\\scriptsize\\href{http://web.usf.edu/FreeAssociation}{Nelson, D. L., McEvoy, C. L., \\& Schreiber, T. A. (1998). The University of South Florida word association, rhyme, and word fragment norms}\\par}\n"
               "\\vspace{0.3cm}\n"
               "{\\scriptsize\\href{https://www.englishclub.com/vocabulary/nouns-uncountable-list.htm}{English Club: Uncountable Nouns List}\\par}\n"
               "\\vspace{0.3cm}\n"
               "{\\scriptsize\\href{http://archives.nd.edu/whitaker/dictpage.htm}{LATIN-ENGLISH DICTIONARY WORDLIST Version 1.97FC by William Whitaker}\\par}\n"
               "\\vspace{0.5cm}\n"
               "\\end{titlepage}\n"
               "\n"
               "\\setcounter{tocdepth}{1}\n"
               "\\renewcommand*\\contentsname{How to make...}\n"
               "\\tableofcontents\n"
               "\\newpage");

    for r in recipes:
        r.print_to_doc(doc)

    try:
        os.remove("TheGreaterBookOfTransmutation.toc")
    except Exception as err:
        traceback.print_tb(err.__traceback__)

    try:
        doc.generate_pdf("TheGreaterBookOfTransmutation")
    except Exception as err:
        traceback.print_tb(err.__traceback__)

    try:
        doc.generate_tex("TheGreaterBookOfTransmutation")
    except Exception as err:
        traceback.print_tb(err.__traceback__)


# Only run if we are the main program, not an import.
if __name__ == "__main__": main()
