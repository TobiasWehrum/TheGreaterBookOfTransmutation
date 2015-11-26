import random
import inflect
import nltk
import data
from nltk.corpus import cmudict
from nltk.corpus import brown
from nltk.corpus import wordnet

DEBUG_SKIP_WORD_ANALYSIS = False
DEBUG_OUTPUT = False

WORD_TYPE_UNKNOWN = ""
WORD_TYPE_NOUN = "N"
WORD_TYPE_ADJECTIVE = "JJ"
# WORD_TYPE_VERB = "VB"
WORD_TYPE_VERB_PRESENT = "VBG"
WORD_TYPE_VERB = "VB"
WORD_TYPES = [WORD_TYPE_NOUN, WORD_TYPE_ADJECTIVE, WORD_TYPE_VERB_PRESENT, WORD_TYPE_VERB]

p = inflect.engine()

uncountable_nouns = 0

def download_corpi():
    nltk.download("brown")
    nltk.download("cmudict")
    nltk.download("wordnet")

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

import time
def find_most_common_word_type(word):
    if DEBUG_SKIP_WORD_ANALYSIS:
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


def has_word_type(word, word_types):
    if DEBUG_SKIP_WORD_ANALYSIS:
        return True

    results = nltk.FreqDist(t for w, t in brown.tagged_words() if w.lower() == word).most_common()
    if len(results) > 0:
        for result in results:
            result_type = result[0]
            for word_type in word_types:
                if result_type.startswith(word_type):
                    return True
    else:
        if DEBUG_OUTPUT:
            print("[has_word_type] Unknown word: " + word)

    return False


def random_weighted_choice(iteration, weight_delegate):
    total_chance = sum(map(weight_delegate, iteration))
    number = random.uniform(0, total_chance)
    for element in iteration:
        number -= weight_delegate(element)
        if number <= 0:
            return element

    return element[-1]


def nounify_first_result(word, default=0):
    result = nounify(word)
    if len(result) == 0:
        if default == 0:
            return word
        else:
            return default

    return result[0][0]()


def nounify(word, type=0):
    if type == 0:
        for t in ["a", "r", "v"]:
            result = nounify(word, t)
            if len(result) > 0:
                return result

        return []

    """ Transform a verb to the closest noun: die -> death """
    synsets = wordnet.synsets(word, pos=type)

    # Word not found
    if not synsets:
        return []

    # Get all verb lemmas of the word
    lemmas = [l for s in synsets for l in s.lemmas() if s.name().split('.')[1] == type]

    # Get related forms
    derivationally_related_forms = [(l, l.derivationally_related_forms()) for l in lemmas]

    # filter only the nouns
    related_noun_lemmas = [l for drf in derivationally_related_forms for l in drf[1] if l.synset().name().split('.')[1] == 'n']

    # Extract the words from the lemmas
    words = [l.name for l in related_noun_lemmas]
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    result = [(w, float(words.count(w))/len_words) for w in set(words)]
    result.sort(key=lambda w: -w[1])

    # return all the possibilities sorted by probability
    return result


def test_nounify():
    print(nounify_first_result("testing"))
    print(nounify_first_result("decide"))
    print(nounify_first_result("deciding"))
    print(nounify_first_result("decided"))
    print(nounify_first_result("conclude"))
    print(nounify_first_result("fast"))
    print(nounify_first_result("feline"))
    print(nounify_first_result("beautiful"))
    print(nounify_first_result("boring"))
    print(nounify_first_result("extreme"))
    print(nounify_first_result("cute"))
    print(nounify_first_result("exploding"))


def is_uncountable_noun(word):
    global uncountable_nouns
    if uncountable_nouns == 0:
        uncountable_nouns = data.load_uncountable_nouns()

    return word in uncountable_nouns
