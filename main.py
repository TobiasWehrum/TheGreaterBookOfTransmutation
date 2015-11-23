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
import nltk
from nltk.corpus import brown
from generator import Markov

RELEASE = False

DEBUG_REDUCE_LATIN_WORD_LIST = True and not RELEASE
data.DEBUG_REDUCE_WORD_LIST = True and not RELEASE
DEBUG_SKIP_WORLD_ANALYSIS = True and not RELEASE
DEBUG_OUTPUT = True
UPDATE_NLTK_CORPI = False


def main():
    if UPDATE_NLTK_CORPI:
        nltk.download("brown")
        nltk.download("cmudict")

    words = data.load_latin_words()
    latin_markov = Markov(3)
    if not DEBUG_REDUCE_LATIN_WORD_LIST:
        for word in words:
            latin_markov.add(word.lower())
    else:
        for word in random.sample(words, 100):
            latin_markov.add(word.lower())

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
    quantity_types = {WORD_TYPE_UNKNOWN: quantity_type_noun,
                      WORD_TYPE_NOUN: quantity_type_noun,
                      WORD_TYPE_ADJECTIVE: quantity_type_adjective,
                      WORD_TYPE_VERB_PRESENT: quantity_type_verb}

    tool_type_vessel = ToolType(["cauldron", "container", "vessel"])
    tool_type_vessel.add(ActionConsuming("Put {material} into {tool}"))
    tool_type_vessel.add(ActionSimple("[Stir|Heat] {tool}").cooldown(2))
    tool_type_vessel.add(ActionSimple("Let {tool} cool down").cooldown(2))
    tool_type_vessel.add(ActionGenerating("Pour out the mixture from {tool} to get the {result}", "{tool} mixture \"{contents}\"", [quantity_type_ounces, quantity_type_spoonful], True).cooldown(2))

    tool_type_smashing = ToolType(["hammer", "stone"])
    tool_type_smashing.add(ActionAdjectivize("Smash {material} with the {tool}", ["smashed", "pulverized"]).cooldown(2))
    tool_type_smashing.add(ActionAdjectivize("Crack {material} with the {tool}", ["cracked", "crushed"]).cooldown(2))

    tool_types = [tool_type_vessel, tool_type_smashing]

    tool_type_default = ToolType()
    # tool_type_default.add(ActionConsuming("Eat {material}").cooldown(2))
    tool_type_default.add(ActionSimple("Wait[| for [a[| very| rather] [short|long] time|[[a second|a minute|an hour|a day]|[2|3|4|5|6|7|8|9|10] [seconds|minutes|hours|days]]]]").cooldown(2))

    end_product = random.choice(list(word_associations.keys()))
    # end_product = "hammer"
    material_names = [t[0] for t in word_associations[end_product]]

    create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default)


def create_recipe(end_product, material_names, quantity_types, tool_types, tool_type_default):
    recipe = Recipe(end_product)

    for material_name in random.sample(material_names, min(4, len(material_names))):
        material_word_type = find_most_common_word_type(material_name)

        # Unknown and length 12? Probably truncated, let's skip it.
        if material_word_type == WORD_TYPE_UNKNOWN and len(material_name) == 12:
            continue

        if material_word_type in quantity_types:
            quantity_type = random.choice(quantity_types[material_word_type])
            amount = quantity_type.random_amount()

            recipe.add_material(Material(material_name, amount, quantity_type))

    for tool_type in random.sample(tool_types, min(2, len(tool_types))):
        tool = Tool(tool_type)
        # if not any(tool.equals(other_tool) for other_tool in recipe.tools):
        recipe.add_tool(tool)

    recipe.add_tool(Tool(tool_type_default))

    recipe.finish()

    print("=======================")
    print()
    recipe.print()


WORD_TYPE_UNKNOWN = ""
WORD_TYPE_NOUN = "NN"
WORD_TYPE_PROPER_NOUN = "NP"
WORD_TYPE_ADJECTIVE = "JJ"
# WORD_TYPE_VERB = "VB"
WORD_TYPE_VERB_PRESENT = "VBG"
WORD_TYPES = [WORD_TYPE_NOUN, WORD_TYPE_ADJECTIVE, WORD_TYPE_VERB_PRESENT]


def find_most_common_word_type(word):
    if DEBUG_SKIP_WORLD_ANALYSIS:
        return random.choice(WORD_TYPES)

    result = nltk.FreqDist(t for w, t in brown.tagged_words() if w.lower() == word).most_common()
    if len(result) > 0:
        result_type = result[0][0]
        for word_type in WORD_TYPES:
            if result_type.startswith(word_type):
                return word_type

        if DEBUG_OUTPUT:
            print("[find_most_common_word_type] Unknown word type: " + result_type + " (for " + word + ")")
    else:
        if DEBUG_OUTPUT:
            print("[find_most_common_word_type] Unknown word: " + word)

    return WORD_TYPE_UNKNOWN

# Only run if we are the main program, not an import.
if __name__ == "__main__": main()
