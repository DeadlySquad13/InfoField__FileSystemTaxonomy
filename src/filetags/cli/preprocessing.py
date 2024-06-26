import logging

# those tags are omitted from being suggested when they are mentioned in .filetags #donotsuggest lines (case insensitive)
# example line:  "#donotsuggest foo bar" -> "foo" and "bar" are never suggested
DONOTSUGGEST_PREFIX = "#donotsuggest "
do_not_suggest_tags = []  # list of lower-case strings


# REFACTOR: Move nine to the agrument.
def get_upto_nine_keys_of_dict_with_highest_value(
    mydict, list_of_tags_to_omit=[], omit_filetags_donotsuggest_tags=False
):
    """
    Takes a dict, sorts it according to their values, and returns up to nine
    values with the highest values.

    Example1: { "key2":45, "key1": 33} -> [ "key1", "key2" ]
    Example2: { "key2":45, "key1": 33, "key3": 99} list_of_tags_to_omit=["key3"] -> [ "key1", "key2" ]

    @param mydict: dictionary holding keys and values
    @param list_of_tags_to_omit: list of strings that should not be part of the returned list
    @param omit_filetags_donotsuggest_tags: boolean that controls whether or not tags are omitted that are mentioned in .filetags #donotsuggest lines
    @param return: list of up to top nine keys according to the rank of their values
    """

    assert mydict.__class__ == dict

    complete_list = sorted(mydict, key=mydict.get, reverse=True)

    logging.debug(
        "get_upto_nine_keys_of_dict_with_highest_value: complete_list: "
        + ", ".join(complete_list)
    )
    if list_of_tags_to_omit:
        logging.debug(
            "get_upto_nine_keys_of_dict_with_highest_value: omitting tags: "
            + ", ".join(list_of_tags_to_omit)
        )
        complete_list = [x for x in complete_list if x not in list_of_tags_to_omit]

    if omit_filetags_donotsuggest_tags:
        # filter all tags that should not be suggested (case insensitive)
        complete_list = [
            x for x in complete_list if x.lower() not in do_not_suggest_tags
        ]

    return sorted(complete_list[:9])
