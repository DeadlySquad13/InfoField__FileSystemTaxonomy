import operator  # for sorting dicts

import colorama  # for colorful output

from filetags.consts import (BETWEEN_TAG_SEPARATOR, FILE_WITH_EXTENSION_REGEX,
                             HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
from filetags.tags.VirtualTags import find_similar_tags


def print_tag_dict(
    tag_dict_reference,
    vocabulary=False,
    sort_index=0,
    print_similar_vocabulary_tags=False,
    print_only_tags_with_similar_tags=False,
):
    """
    Takes a dictionary which holds tag names and their occurrence and prints it to stdout.
    Tags that appear also in the vocabulary get marked in the output.

    @param tag_dict: a dictionary holding tags and their occurrence number
    @param vocabulary: array of tags from controlled vocabulary or False
    """

    tag_dict = {}
    tag_dict = tag_dict_reference

    # determine maximum length of strings for formatting:
    if len(tag_dict) > 0:
        maxlength_tags = max(len(s) for s in list(tag_dict.keys())) + len(
            HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        )
        maxlength_count = len(str(abs(max(tag_dict.values()))))
    else:
        maxlength_tags = len(HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
        maxlength_count = 5

    if maxlength_count < 5:
        maxlength_count = 5

    hint_for_being_in_vocabulary = ""
    similar_tags = ""
    if vocabulary:
        print(
            '\n  (Tags marked with "'
            + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE.strip()
            + '" appear in your vocabulary.)'
        )
    print(
        "\n {0:{1}} : {2:{3}}".format("count", maxlength_count, "tag", maxlength_tags)
    )
    print(" " + "-" * (maxlength_tags + maxlength_count + 7))
    for tuple in sorted(list(tag_dict.items()), key=operator.itemgetter(sort_index)):
        # sort dict of (tag, count) according to sort_index

        if vocabulary and tuple[0] in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ""

        similar_tags_list = []
        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(
                set(tag_dict.keys()).union(set(vocabulary))
            )  # unified elements of both lists
            similar_tags_list = find_similar_tags(tuple[0], tags_for_comparing)
            if similar_tags_list:
                similar_tags = (
                    "      (similar to:  " + ", ".join(similar_tags_list) + ")"
                )
            else:
                similar_tags = ""
        else:
            similar_tags = ""

        if (
            print_only_tags_with_similar_tags and similar_tags_list
        ) or not print_only_tags_with_similar_tags:
            print(
                " {0:{1}} : {2:{3}}   {4}".format(
                    tuple[1],
                    maxlength_count,
                    tuple[0] + hint_for_being_in_vocabulary,
                    maxlength_tags,
                    similar_tags,
                )
            )

    print("")


def print_tag_set(tag_set, vocabulary=False, print_similar_vocabulary_tags=False):
    """
    Takes a set which holds tag names and prints it to stdout.
    Tags that appear also in the vocabulary get marked in the output.

    @param tag_set: a set holding tags
    @param vocabulary: array of tags from controlled vocabulary or False
    @param print_similar_vocabulary_tags: if a vocabulary is given and
        tags are similar to it, print a list of them
    """

    # determine maximum length of strings for formatting:
    maxlength_tags = max(len(s) for s in tag_set) + len(
        HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
    )

    hint_for_being_in_vocabulary = ""
    if vocabulary:
        print(
            '\n  (Tags marked with "'
            + HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE.strip()
            + '" appear in your vocabulary.)\n'
        )

    for tag in sorted(tag_set):

        if vocabulary and tag in vocabulary:
            hint_for_being_in_vocabulary = HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE
        else:
            hint_for_being_in_vocabulary = ""

        if vocabulary and print_similar_vocabulary_tags:
            tags_for_comparing = list(
                tag_set.union(set(vocabulary))
            )  # unified elements of both lists
            similar_tags_list = find_similar_tags(tag, tags_for_comparing)
            if similar_tags_list:
                similar_tags = (
                    "      (similar to:  " + ", ".join(similar_tags_list) + ")"
                )
            else:
                similar_tags = ""
        else:
            similar_tags = ""

        print(
            "  {0:{1}}   {2}".format(
                tag + hint_for_being_in_vocabulary, maxlength_tags, similar_tags
            )
        )

    print("")


# - Beautified.
def get_tag_visual(tags_for_visual=None):
    """
    Returns a visual representation of a tag. If the optional tags_for_visual
    is given, write the list of those tags into to the tag as well.

    @param tags_for_visual: list of strings with tags
    @param return: string with a multi-line representation of a visual tag
    """

    if not tags_for_visual:
        tags = " ? "
    else:
        tags = BETWEEN_TAG_SEPARATOR.join(sorted(tags_for_visual))

    style = colorama.Back.BLACK + colorama.Fore.GREEN

    length = len(tags)
    visual = (
        "         "
        + style
        + ".---"
        + "-" * length
        + "--,"
        + colorama.Style.RESET_ALL
        + " \n"
        + "        "
        + style
        + "| o  "
        + colorama.Style.BRIGHT
        + tags
        + colorama.Style.NORMAL
        + "  |"
        + colorama.Style.RESET_ALL
        + " \n"
        + "         "
        + style
        + "`---"
        + "-" * length
        + "--'"
        + colorama.Style.RESET_ALL
        + " "
    )

    return visual
