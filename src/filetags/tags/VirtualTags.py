import difflib  # for good enough matching words

from filetags.cli.preprocessing import locate_and_parse_controlled_vocabulary
from filetags.tags.services.TagLocalFilesystem import extract_tags_from_filename


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
