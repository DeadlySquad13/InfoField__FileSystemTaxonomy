import logging

import colorama  # for colorful output


def print_tag_shortcut_with_numbers(
    tag_list, tags_get_added=True, tags_get_linked=False
):
    """A list of tags from the list are printed to stdout. Each tag
    gets a number associated which corresponds to the position in the
    list (although starting with 1).

    @param tag_list: list of string holding the tags
    @param tags_get_added: True if tags get added, False otherwise
    @param return: -
    """

    if tags_get_added:
        if len(tag_list) < 9:
            hint_string = "Previously used tags in this directory:"
        else:
            hint_string = "Top nine previously used tags in this directory:"
    elif tags_get_linked:
        if len(tag_list) < 9:
            hint_string = "Used tags in this directory:"
        else:
            hint_string = "Top nine used tags in this directory:"
    else:
        if len(tag_list) < 9:
            hint_string = "Possible tags to be removed:"
        else:
            hint_string = "Top nine possible tags to be removed:"
    print("\n  " + colorama.Style.DIM + hint_string + colorama.Style.RESET_ALL)

    count = 1
    list_of_tag_hints = []
    for tag in tag_list:
        list_of_tag_hints.append(tag + " (" + str(count) + ")")
        count += 1
    try:
        print("    " + " ⋅ ".join(list_of_tag_hints))
    except UnicodeEncodeError:
        logging.debug(
            'ERROR: I got an UnicodeEncodeError when displaying "⋅" (or list_of_tag_hints) '
            + 'but I re-try with "|" as a separator instead ...'
        )
        print("    " + " | ".join(list_of_tag_hints))
    print("")  # newline at end


def check_for_possible_shortcuts_in_entered_tags(usertags, list_of_shortcut_tags):
    """
    Returns tags if the only tag is not a shortcut (entered as integer).
    Returns a list of corresponding tags if it's an integer.

    @param usertags: list of entered tags from the user, e.g., [u'23']
    @param list_of_shortcut_tags: list of possible shortcut tags, e.g., [u'bar', u'folder1', u'baz']
    @param return: list of tags which were meant by the user, e.g., [u'bar', u'baz']
    """

    assert usertags.__class__ == list
    assert list_of_shortcut_tags.__class__ == list

    foundtags = (
        []
    )  # collect all found tags which are about to return from this function

    for currenttag in usertags:
        try:
            logging.debug("tag is an integer; stepping through the integers")
            found_shortcut_tags_within_currenttag = (
                []
            )  # collects the shortcut tags of a (single) currenttag
            for character in list(currenttag):
                # step through the characters and find out if it consists of valid indexes of the list_of_shortcut_tags:
                if currenttag in foundtags:
                    # we already started to step through currenttag, character by character, and found out (via
                    # IndexError) that the whole currenttag is a valid tag and added it already to the tags-list.
                    # Continue with the next tag from the user instead of continue to step through the characters:
                    continue
                try:
                    # try to append the index element to the list of found shortcut tags so far (and risk an IndexError):
                    found_shortcut_tags_within_currenttag.append(
                        list_of_shortcut_tags[int(character) - 1]
                    )
                except IndexError:
                    # IndexError tells us that the currenttag contains a character which is not a valid index of
                    # list_of_shortcut_tags. Therefore, the whole currenttag is a valid tag and not a set of
                    # indexes for shortcuts:
                    foundtags.append(currenttag)
                    continue
            if currenttag not in foundtags:
                # Stepping through all characters without IndexErrors
                # showed us that all characters were valid indexes for
                # shortcuts and therefore extending those shortcut tags to
                # the list of found tags:
                logging.debug("adding shortcut tags of number(s) %s" % currenttag)
                foundtags.extend(found_shortcut_tags_within_currenttag)
        except ValueError:
            # ValueError tells us that one character is not an integer. Therefore, the whole currenttag is a valid tag:
            logging.debug("whole tag is a normal tag")
            foundtags.append(currenttag)

    return foundtags
