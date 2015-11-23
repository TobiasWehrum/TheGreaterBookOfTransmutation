import random
import inflect
import nltk
from nltk.corpus import cmudict
from nltk.corpus import brown

DEBUG_SKIP_WORLD_ANALYSIS = False
DEBUG_OUTPUT = False

WORD_TYPE_UNKNOWN = ""
WORD_TYPE_NOUN = "NN"
WORD_TYPE_PROPER_NOUN = "NP"
WORD_TYPE_ADJECTIVE = "JJ"
# WORD_TYPE_VERB = "VB"
WORD_TYPE_VERB_PRESENT = "VBG"
WORD_TYPES = [WORD_TYPE_NOUN, WORD_TYPE_ADJECTIVE, WORD_TYPE_VERB_PRESENT]

p = inflect.engine()


def download_corpi():
    nltk.download("brown")
    nltk.download("cmudict")

def starts_with_vowel_sound(word, pronunciations=cmudict.dict()):
    for syllables in pronunciations.get(word, []):
        return syllables[0][-1].isdigit()  # use only the first one


def get_indefinite_article(word):
    return "an" if starts_with_vowel_sound(word) else "a"


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
