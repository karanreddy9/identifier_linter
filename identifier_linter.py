import getopt
import os
import shutil
import re
import sys
import git.exc

from tree_sitter import Language, Parser
from spellchecker import SpellChecker
from word2number import w2n
from git import Repo

# Language.build_library(
#     # Store the library in the `build` directory
#     'build/my-languages.so',
#
#     # Include one or more languages
#     [
#         './tree-sitter-go',
#         './tree-sitter-javascript',
#         './tree-sitter-python',
#         './tree-sitter-ruby'
#     ]
# )

GO_LANGUAGE = Language('build/my-languages.so', 'go')
JS_LANGUAGE = Language('build/my-languages.so', 'javascript')
PY_LANGUAGE = Language('build/my-languages.so', 'python')
RB_LANGUAGE = Language('build/my-languages.so', 'ruby')

spell = SpellChecker()


def clone_repo(github_url):
    if os.path.exists("./cloned_repo"):
        shutil.rmtree("./cloned_repo")
    try:
        Repo.clone_from(github_url, "./cloned_repo")
    except git.exc.GitCommandError:
        print("repository '" + github_url + "' does not exist")


def read_files():
    f1 = open("output1.txt", "w")
    f1.close()

    f2 = open("output2.txt", "w")
    f2.close()

    for root, dirs, files in os.walk("./cloned_repo"):
        for file in files:
            fy = "---------------------------------------------------------\nBelow is the identifier list for '" \
                 + file + "'\n---------------------------------------------------------\n"
            f = open("output1.txt", "a")
            g = open("output2.txt", "a")
            if file.endswith(".py"):
                file_language = PY_LANGUAGE
            elif file.endswith(".js"):
                file_language = JS_LANGUAGE
            elif file.endswith(".go"):
                file_language = GO_LANGUAGE
            elif file.endswith(".rb"):
                file_language = RB_LANGUAGE
            else:
                continue
            f.write(fy)
            g.write(fy)
            f.close()
            g.close()

            file_path = (os.path.join(root, file))
            file_code = open(file_path, "r").read()

            parser = Parser()
            parser.set_language(file_language)

            tree = parser.parse(bytes(file_code, "utf8"))
            root_node = tree.root_node

            print_nodes(root_node, file_code, file)

            f3 = open("output1.txt", "a")
            f3.write("\n")
            f3.close()

            f4 = open("output2.txt", "a")
            f4.write("\n")
            f4.close()


def check_spelling(words):
    misspelled = spell.unknown(words)
    dict_word = 1
    for word in misspelled:
        if spell.correction(word):
            dict_word = 0
            break

    return dict_word


def check_numeric_identifier(words):
    numeric_identifier = 1
    for word in words:
        try:
            w2n.word_to_num(word)
        except ValueError:
            numeric_identifier = 0

    return numeric_identifier


def validate_identifier(identifier_name, identifier_details):
    f = open("output2.txt", "a")

    prev_ind = 0
    identifier_words = []
    numeric_words = []
    short_identifiers = ['c', 'd', 'e', 'g', 'i', 'in', 'inOut', 'j', 'k', 'm', 'n', 'o', 'out', 't', 'x', 'y', 'z']
    for i in range(1, len(identifier_name)):
        if identifier_name[i].isupper():
            identifier_words.append(identifier_name[prev_ind:i])
            prev_ind = i
    identifier_words.append(identifier_name[prev_ind:])

    prev_ind = 0
    for i in range(1, len(identifier_name)):
        if identifier_name[i] == "_":
            numeric_words.append(identifier_name[prev_ind:i])
            prev_ind = i
    numeric_words.append(identifier_name[prev_ind+1:])

    identifier_length = 0
    for w in identifier_words:
        identifier_length += len(w)

    dict_word = check_spelling(identifier_words)
    numeric_word = check_numeric_identifier(numeric_words)

    if numeric_word == 1:
        f.write(identifier_details + " -> Identifiers should not be composed entirely of numeric words or numbers.\n")
    elif re.search(r"\b.*[A-Z]{2}[a-zA-Z]*\b", identifier_name):
        f.write(identifier_details + " -> Identifiers should be appropriately capitalized.\n")
    elif re.search(r"\b[a-z][a-z0-9_]*\b", identifier_name) and not re.search(r"^.*[_][a-z0-9]+$", identifier_name) \
            and dict_word == 0 and len(identifier_name) >= 8:
        f.write(identifier_details + " -> Identifiers should be appropriately capitalized.\n")
    elif not re.search("^(?!.*[_]{2})[a-zA-Z0-9_.]+$", identifier_name):
        f.write(identifier_details + " -> Consecutive underscores should not be used in identifier names.\n")
    elif re.search(r"^.*[_][a-z0-9].*[_]+$", identifier_name):
        f.write(identifier_details + " -> Identifiers should not have either leading or trailing underscores.\n")
    elif dict_word == 0 and not re.search(r"^.*[_][a-z0-9]+$", identifier_name):
        f.write(identifier_details +
                " -> Identifier names should be composed of words found in the dictionary and abbreviations, and "
                "acronyms, that are more commonly used than the unabbreviated form.\n")
    elif len(identifier_words) > 4:
        f.write(identifier_details + " -> Identifier names should be composed of no more than four words "
                                     "or abbreviations.\n")
    elif identifier_length > 25:
        f.write(identifier_details + " -> Long identifier names should be avoided where possible\n")
    elif re.search(r"^.*[A-Z0-9][_].*[a-z0-9]+$", identifier_name) or re.search(r"^.*[a-z0-9][_].*[A-Z0-9]+$",
                                                                                identifier_name):
        f.write(identifier_details + " -> Identifiers should not consist of non-standard mixes of upper and lower "
                                     "case characters.\n")
    elif len(identifier_name) < 8 and identifier_name not in short_identifiers:
        f.write(identifier_details + " -> Identifiers should not consist of fewer than eight characters, with the "
                                     "exception of: c, d, e, g, i, in, inOut, j, k, m, n, o, out, t, x, y, z\n")

    f.close()


def print_nodes(node, file_program, output_file):
    if node.children:
        for n in node.children:
            print_nodes(n, file_program, output_file)
    else:
        if node.type == 'identifier':
            identifier_line = file_program.splitlines()[node.start_point[0]]
            identifier_name = identifier_line[node.start_point[1]:node.end_point[1]]
            f = open("output1.txt", "a")
            identifier_details = identifier_name + " (" + ', '.join(map(str, node.start_point)) \
                                 + ") (" + ', '.join(map(str, node.end_point)) + ")"
            f.write(identifier_details + "\n")
            f.close()

            validate_identifier(identifier_name, identifier_details)


def main(argv):
    input_url = ''

    if len(argv) == 0:
        print("No input github URL provided! Cloning the default repo")
        clone_repo("https://github.com/karanreddy9/test_repo.git")
        read_files()
        sys.exit(2)
    elif len(argv) != 2:
        print("Usage: python identifier_linter.py -i <github url>")
        print("Example: python identifier_linter.py -i https://github.com/karanreddy9/test_repo.git")
        sys.exit(2)
    try:
        opts, args = getopt.getopt(argv, "hi:", ["input_file="])
    except getopt.GetoptError:
        print("Usage: python identifier_linter.py -i <github url>")
        print("Example: python identifier_linter.py -i https://github.com/karanreddy9/test_repo.git")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("Usage: python identifier_linter.py -i <github url>")
            print("Example: python identifier_linter.py -i https://github.com/karanreddy9/test_repo.git")
            sys.exit()
        elif opt in ("-i", "--input_file"):
            input_url = arg

    clone_repo(input_url)
    read_files()


if __name__ == "__main__":
    main(sys.argv[1:])
