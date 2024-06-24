# import win32com
import logging
import os
import re
import time

from filetags.cli.parser import CliOptions
from filetags.consts import YYYY_MM_DD_PATTERN


def extract_iso_datestamp_from_filename(filename):
    """
    Returns array of year, month, day if filename starts with
    YYYY-MM-DD datestamp. Returns empty array else.
    """

    components = re.match(YYYY_MM_DD_PATTERN, filename)
    if components:
        return [components.group(1), components.group(2), components.group(3)]
    else:
        return []


# REFACTOR: Abstract tag methods.
# REFACTOR: Remove use_cache.
def get_files_with_metadata(
    startdir=os.getcwd(),
    use_cache=True,
    cache_of_files_with_metadata={},
    options: CliOptions = None,
):
    """
    Traverses the file system starting with given directory,
    returns list: filename and metadata-dict:

    The result is stored in the global dict as
    cache_of_files_with_metadata[startdir] with dict elements like:
      'filename': '2018-03-18 this is a file name -- tag1 tag2.txt',
      'filetags': ['tag1', 'tag2'],
      'path': '/this/is -- tag1/the -- tag3/path',
      'alltags': ['tag1', 'tag2', 'tag3'],
      'ctime': time.struct_time,
      'datestamp': ['2018', '03', '18'],

    @param use_cache: FOR FUTURE USE; default = True
    @param return: list of filenames and metadata-dict
    """

    assert os.path.isdir(startdir)

    logging.debug(
        "get_files_with_metadata called with startdir [%s], cached startdirs [%s]"
        % (startdir, str(len(list(cache_of_files_with_metadata.keys()))))
    )

    # REFACTOR: Move out of this function.
    if use_cache and len(cache_of_files_with_metadata) > 0:
        logging.debug(
            "found "
            + str(len(cache_of_files_with_metadata))
            + " files in cache for files"
        )
        return cache_of_files_with_metadata

    else:
        cache = []
        for root, dirs, files in os.walk(startdir):

            # logging.debug('get_files_with_metadata: root [%s]' % root)  # LOTS of debug output
            for filename in files:

                absfilename = os.path.abspath(os.path.join(root, filename))
                # logging.debug('get_files_with_metadata: file [%s]' % absfilename)  # LOTS of debug output
                path, basename = os.path.split(absfilename)
                if os.path.islink(absfilename):
                    # link files do not have ctime and must be dereferenced before. However, they can link to another link file or they can be broken.
                    # Design decision: ignoring link files alltogether. Their source should speak for themselves.
                    logging.debug(
                        "get_files_with_metadata: file [%s] is link to [%s] and gets ignored here"
                        % (
                            absfilename,
                            os.path.join(
                                os.path.dirname(absfilename), os.readlink(absfilename)
                            ),
                        )
                    )
                    continue
                else:
                    ctime = time.localtime(os.path.getctime(absfilename))

                cache.append(
                    {
                        "filename": basename,
                        "filetags": extract_tags_from_filename(basename),
                        "path": path,
                        "alltags": extract_tags_from_path(absfilename),
                        "ctime": ctime,
                        "datestamp": extract_iso_datestamp_from_filename(basename),
                    }
                )

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
            "Writing " + str(len(cache)) + " files in cache for directory: " + startdir
        )
        if use_cache:
            cache_of_files_with_metadata[startdir] = cache
        return cache
