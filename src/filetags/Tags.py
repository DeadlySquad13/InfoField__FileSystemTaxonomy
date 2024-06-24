import logging
import os
import difflib  # for good enough matching words
import re
import colorama  # for colorful output

from filetags.consts import (BETWEEN_TAG_SEPARATOR,
                             FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX,
                             FILE_WITH_EXTENSION_REGEX,
                             FILE_WITH_TAGS_REGEX,
                             FILE_WITH_TAGS_REGEX_FILENAME_INDEX,
                             FILE_WITH_TAGS_REGEX_EXTENSION_INDEX,
                             FILE_WITH_TAGS_REGEX_TAGLIST_INDEX,
                             FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX,
                             FILENAME_TAG_SEPARATOR,
                             HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE)
from filetags.file_operations import split_up_filename, is_lnk_file
from filetags.cli.preprocessing import locate_and_parse_controlled_vocabulary
from filetags.cli.parser import get_cli_options

# REFACTOR: Move to functions as param.
options = get_cli_options()

# # TagLocalFilesystem
def contains_tag(filename, tagname=False):
    """
    Returns true if tagname is a tag within filename. If tagname is
    empty, return if filename contains any tag at all.

    @param filename: an unicode string containing a file name
    @param tagname: (optional) an unicode string containing a tag name
    @param return: True|False
    """

    assert filename.__class__ == str
    if tagname:
        assert tagname.__class__ == str

    filename, dirname, basename, basename_without_lnk = split_up_filename(filename)

    components = re.match(FILE_WITH_TAGS_REGEX, os.path.basename(basename_without_lnk))

    if not tagname:
        return components is not None
    elif not components:
        logging.debug("file [%s] does not match FILE_WITH_TAGS_REGEX" % filename)
        return False
    else:
        tags = components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(
            BETWEEN_TAG_SEPARATOR
        )
        return tagname in tags


def extract_tags_from_filename(filename):
    """
    Returns list of tags contained within filename. If no tag is
    found, return False.

    @param filename: an unicode string containing a file name
    @param return: list of tags
    """

    assert filename.__class__ == str

    filename, dirname, basename, basename_without_lnk = split_up_filename(filename)

    components = re.match(FILE_WITH_TAGS_REGEX, basename_without_lnk)

    if not components:
        return []
    else:
        return components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(
            BETWEEN_TAG_SEPARATOR
        )


def extract_tags_from_path(path):
    """
    Returns list of all tags contained within the absolute path that may contain
    directories and an optional file. If no tag is found, return empty list.

    @param path: an unicode string containing a path
    @param return: list of tags
    """

    def splitall(path):
        """
        Snippet from:
            https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch04s16.html

        >>> splitall('a/b/c')
        ['a', 'b', 'c']
        >>> splitall('/a/b/c/')
        ['/', 'a', 'b', 'c', '']
        >>> splitall('/')
        ['/']
        >>> splitall('C:')
        ['C:']
        >>> splitall('C:\\')
        ['C:\\']
        >>> splitall('C:\\a')
        ['C:\\', 'a']
        >>> splitall('C:\\a\\')
        ['C:\\', 'a', '']
        >>> splitall('C:\\a\\b')
        ['C:\\', 'a', 'b']
        >>> splitall('a\\b')
        ['a', 'b']
        """

        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    assert path.__class__ == str

    tags = []
    abspath = os.path.abspath(path)
    for item in splitall(abspath):
        itemtags = extract_tags_from_filename(item)
        for currentitemtag in itemtags:
            if currentitemtag not in tags:
                tags.append(currentitemtag)
    return tags


def adding_tag_to_filename(filename, tagname):
    """
    Returns string of file name with tagname as additional tag.

    @param filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename containing tagname
    """

    assert filename.__class__ == str
    assert tagname.__class__ == str

    filename, dirname, basename, basename_without_lnk = split_up_filename(filename)

    if contains_tag(basename_without_lnk) is False:
        logging.debug(
            "adding_tag_to_filename(%s, %s): no tag found so far" % (filename, tagname)
        )

        components = re.match(FILE_WITH_EXTENSION_REGEX, basename_without_lnk)
        if components:
            old_basename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
            if is_lnk_file(filename):
                return os.path.join(
                    dirname,
                    old_basename
                    + FILENAME_TAG_SEPARATOR
                    + tagname
                    + "."
                    + extension
                    + ".lnk",
                )
            else:
                return os.path.join(
                    dirname,
                    old_basename + FILENAME_TAG_SEPARATOR + tagname + "." + extension,
                )
        else:
            # filename has no extension
            if is_lnk_file(filename):
                return os.path.join(
                    dirname,
                    basename_without_lnk + FILENAME_TAG_SEPARATOR + tagname + ".lnk",
                )
            else:
                return os.path.join(
                    dirname, basename + FILENAME_TAG_SEPARATOR + tagname
                )

    elif contains_tag(basename_without_lnk, tagname):
        logging.debug(
            "adding_tag_to_filename(%s, %s): tag already found in filename"
            % (filename, tagname)
        )

        return filename

    else:
        logging.debug(
            "adding_tag_to_filename(%s, %s): add as additional tag to existing list of tags"
            % (filename, tagname)
        )

        components = re.match(FILE_WITH_EXTENSION_REGEX, basename_without_lnk)
        new_filename = False
        if components:
            old_basename = components.group(FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX)
            extension = components.group(FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX)
            new_filename = os.path.join(
                dirname,
                old_basename + BETWEEN_TAG_SEPARATOR + tagname + "." + extension,
            )
        else:
            new_filename = os.path.join(
                dirname, basename + BETWEEN_TAG_SEPARATOR + tagname
            )
        if is_lnk_file(filename):
            return new_filename + ".lnk"
        else:
            return new_filename


def removing_tag_from_filename(orig_filename, tagname):
    """
    Returns string of file name with tagname removed as tag.

    @param orig_filename: an unicode string containing a file name
    @param tagname: an unicode string containing a tag name
    @param return: an unicode string of filename without tagname
    """

    assert orig_filename.__class__ == str
    assert tagname.__class__ == str

    if not contains_tag(orig_filename, tagname):
        return orig_filename

    filename, dirname, basename, basename_without_lnk = split_up_filename(orig_filename)
    components = re.match(FILE_WITH_TAGS_REGEX, basename_without_lnk)

    if not components:
        logging.debug("file [%s] does not match FILE_WITH_TAGS_REGEX" % orig_filename)
        return orig_filename
    else:
        tags = components.group(FILE_WITH_TAGS_REGEX_TAGLIST_INDEX).split(
            BETWEEN_TAG_SEPARATOR
        )
        old_filename = components.group(FILE_WITH_TAGS_REGEX_FILENAME_INDEX)
        extension = components.group(FILE_WITH_TAGS_REGEX_EXTENSION_INDEX)
        if not extension:
            extension = ""
        else:
            extension = "." + extension

        new_filename = False
        if len(tags) < 2:
            logging.debug(
                "given tagname is the only tag -> remove all tags and FILENAME_TAG_SEPARATOR as well"
            )
            new_filename = old_filename + extension
        else:
            # still tags left
            new_filename = (
                old_filename
                + FILENAME_TAG_SEPARATOR
                + BETWEEN_TAG_SEPARATOR.join([tag for tag in tags if tag != tagname])
                + extension
            )

        if is_lnk_file(orig_filename):
            return new_filename + ".lnk"
        else:
            return new_filename


cache_of_tags_by_folder = {}


# REFACTOR: Remove use_cache.
def get_tags_from_files_and_subfolders(startdir=os.getcwd(), use_cache=True, cache_of_files_with_metadata={}):
    """
    Traverses the file system starting with given directory,
    returns dict of all tags (including starttags) of all file.
    Uses cache_of_files_with_metadata of use_cache is true and
    cache is populated with same startdir.

    @param use_cache: FOR FUTURE USE
    @param return: dict of tags and their number of occurrence
    """

    # add ", starttags=False" to parameters to enable this feature in future
    starttags = False

    assert os.path.isdir(startdir)

    if not starttags:
        tags = {}
    else:
        assert starttags.__class__ == dict
        tags = starttags

    logging.debug(
        "get_tags_from_files_and_subfolders called with startdir [%s], cached startdirs [%s]"
        % (startdir, str(len(list(cache_of_tags_by_folder.keys()))))
    )

    if use_cache and startdir in list(cache_of_tags_by_folder.keys()):
        logging.debug(
            "get_tags_from_files_and_subfolders: found "
            + str(len(cache_of_tags_by_folder[startdir]))
            + " tags in cache for directory: "
            + startdir
        )
        return cache_of_tags_by_folder[startdir]

    elif use_cache and startdir in cache_of_files_with_metadata.keys():
        logging.debug(
            "get_tags_from_files_and_subfolders: using cache_of_files_with_metadata instead of traversing file system again"
        )
        cachedata = cache_of_files_with_metadata[startdir]

        # FIX: Check if tags are extracted from dirnames as in traversal algorithm below.
        for entry in cachedata:
            for tag in entry["alltags"]:
                tags = add_tag_to_countdict(tag, tags)

    else:

        for root, dirs, files in os.walk(startdir):

            # logging.debug('get_tags_from_files_and_subfolders: root [%s]' % root)  # LOTS of debug output

            for filename in files:
                for tag in extract_tags_from_filename(filename):
                    tags = add_tag_to_countdict(tag, tags)

            for dirname in dirs:
                for tag in extract_tags_from_filename(dirname):
                    tags = add_tag_to_countdict(tag, tags)

            # Enable recursive directory traversal for specific options:
            if not (
                options.recursive
                and (
                    options.list_tags_by_alphabet
                    or options.list_tags_by_number
                    or options.list_unknown_tags
                    or options.tag_gardening
                )
            ):
                break  # do not loop

    logging.debug(
        "get_tags_from_files_and_subfolders: Writing "
        + str(len(list(tags.keys())))
        + " tags in cache for directory: "
        + startdir
    )
    if use_cache:
        cache_of_tags_by_folder[startdir] = tags
    return tags


# # Virtual Tags
def get_unique_tags_from_filename(filename):
    """
    Extracts tags that occur in the array of arrays "unique_tags".

    @param filename: string containing one file name
    @param return: list of found tags
    """

    filetags = extract_tags_from_filename(filename)
    result = []
    for tag in filetags:
        for taggroup in unique_tags:
            if tag in taggroup:
                result.append(tag)
    return result


def find_similar_tags(tag, tags):
    """
    Returns a list of entries of tags that are similar to tag (but not same as tag)

    @param tag: a (unicode) string that represents a tag
    @param tags: a list of (unicode) strings
    @param return: list of tags that are similar to tag
    """

    assert tag.__class__ == str
    assert tags.__class__ == list

    similar_tags = difflib.get_close_matches(tag, tags, n=999, cutoff=0.7)
    close_but_not_exact_matches = []

    # omit exact matches
    # FIX: This can be done in one eloquent line -> refactor.
    for match in similar_tags:
        if match != tag:
            close_but_not_exact_matches.append(match)

    return close_but_not_exact_matches


def list_unknown_tags(file_tag_dict):
    """
    Traverses the file system, extracts all tags, prints tags that are found
    in file names which are not found in the controlled vocabulary file .filetags

    @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
    """

    # REFACTOR: False as a param?
    vocabulary = locate_and_parse_controlled_vocabulary(False)

    # filter out known tags from tag_dict
    unknown_tag_dict = {
        key: value
        for key, value in list(file_tag_dict.items())
        if key not in vocabulary
    }

    if unknown_tag_dict:
        print_tag_dict(unknown_tag_dict, vocabulary)
    else:
        print(
            "\n  "
            + str(len(file_tag_dict))
            + " different tags were found in file names which are all"
            + " part of your .filetags vocabulary (consisting of "
            + str(len(vocabulary))
            + " tags).\n"
        )

    return unknown_tag_dict


def filter_files_matching_tags(allfiles, tags):
    """
    Returns a list of file names that contain all given tags.

    @param allfiles: array of file names
    @param tags: array of tags
    @param return: list of file names that contain all tags
    """

    return [
        x for x in allfiles if set(extract_tags_from_filename(x)).issuperset(set(tags))
    ]


# REFACTOR: Move to data_structures and reuse here as a simple function call.
def add_tag_to_countdict(tag, tags):
    """
    Takes a tag (string) and a dict. Returns the dict with count value increased by one

    @param tag: a (unicode) string
    @param tags: dict of tags
    @param return: dict of tags with incremented counter of tag (or 0 if new)
    """

    assert tag.__class__ == str
    assert tags.__class__ == dict

    if tag in list(tags.keys()):
        tags[tag] = tags[tag] + 1
    else:
        tags[tag] = 1

    return tags


# ## Printing
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
def _get_tag_visual(tags_for_visual=None):
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


# ## Shortcuts
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
