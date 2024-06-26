import logging
import os
import re

from filetags.cli.parser.options import CliOptions
from filetags.consts import (BETWEEN_TAG_SEPARATOR, FILE_WITH_EXTENSION_REGEX,
                             FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX,
                             FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX,
                             FILE_WITH_TAGS_REGEX,
                             FILE_WITH_TAGS_REGEX_EXTENSION_INDEX,
                             FILE_WITH_TAGS_REGEX_FILENAME_INDEX,
                             FILE_WITH_TAGS_REGEX_TAGLIST_INDEX,
                             FILENAME_TAG_SEPARATOR)
from filetags.file_operations import is_lnk_file, split_up_filename
from filetags.tags.utils import add_tag_to_countdict


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
# FIX: Pass cache in usages as much as possible.
def get_tags_from_files_and_subfolders(
    startdir=os.getcwd(),
    use_cache=True,
    cache_of_files_with_metadata={},
    options: CliOptions = {},
):
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
                options.get('recursive')
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
