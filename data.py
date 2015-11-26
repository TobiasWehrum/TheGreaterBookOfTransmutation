import os
import sys
import locale
import re


DEBUG_REDUCE_WORD_LIST = False
BASE_DIR = os.path.dirname(sys.argv[0])
DATA_DIR = os.path.join(BASE_DIR, "data")
USF_FREE_ASSOCIATION_DIR = os.path.join(DATA_DIR, "usf_FreeAssociation_B")
LATIN_WORDS_FILE = os.path.join(DATA_DIR, "latin_words", "DICTPAGE.RAW")
UNCOUNTABLE_NOUNS_DIR = os.path.join(DATA_DIR, "uncountable_nouns")


def load_usf_free_association_files():
    result = {}
    # split_pattern = re.compile("\s*")
    # match_number = re.compile("(0\.[0-9]+)(?=(?:0\.|$))")

    for file in files_in_folder(USF_FREE_ASSOCIATION_DIR, "html"):
        target = ""
        primes = []

        for line in file:
            if line.startswith("<"):
                continue

            if len(line.strip()) == 0:
                continue

            if line.startswith(" NO. OF CUES"):
                result[target] = primes
                target = ""
                primes = []
                continue

            if len(target) == 0:
                target = line[0:13].strip().lower()
            else:
                prime = line[0:13].strip().lower()
                fsg = locale.atof(line[13:17])
                primes.append((prime, fsg))

            # elements = split_pattern.split(line)
            # number_match = match_number.search(elements[1])
            # if number_match:
            #     print(number_match.groups(0)[0])
            # else:
            #     print(elements[1])

        file.close()
        if DEBUG_REDUCE_WORD_LIST:
            break

    print("Read " + str(len(result)) + " targets from USF FreeAssociation data files.")

    return result


def load_latin_words():
    result = []
    match_pattern = re.compile("\w+")

    file = open(LATIN_WORDS_FILE, 'r')

    for line in file:
        word_match = match_pattern.search(line)
        if word_match:
            word = word_match.group()
            result.append(word)

    file.close()
    return result


def load_uncountable_nouns():
    result = []
    for file in files_in_folder(UNCOUNTABLE_NOUNS_DIR, "txt"):
        for line in file:
            result.append(line[:-1])

    file.close()
    return result


def files_in_folder(folder, extension=""):
    for file_name in os.listdir(folder):
        if len(extension) == 0 or file_name.endswith("." + extension):
            yield open(os.path.join(folder, file_name), 'r')
