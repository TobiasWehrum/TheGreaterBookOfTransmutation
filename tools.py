from nltk.corpus import cmudict


def starts_with_vowel_sound(word, pronunciations=cmudict.dict()):
    for syllables in pronunciations.get(word, []):
        return syllables[0][-1].isdigit()  # use only the first one


def get_indefinite_article(word):
    return "an" if starts_with_vowel_sound(word) else "a"
