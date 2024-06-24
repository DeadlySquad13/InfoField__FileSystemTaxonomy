# import win32com
import errno
import logging
import os
import re
import time

from filetags.cli.parser import CliOptions
from filetags.consts import (IS_WINDOWS, TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS,
                             YYYY_MM_DD_PATTERN)
from filetags.utils.logging import error_exit


# # Metadata.
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


# # Links.
def find_unique_alternative_to_file(filename):
    """
    @param filename: string containing one file name which does not exist
    @param return: False or filename that starts with same substring within this directory
    """

    logging.debug(
        "file type error for file [%s] in folder [%s]: file type: is file? %s  -  is dir? %s  -  is mount? %s"
        % (
            filename,
            os.getcwd(),
            str(os.path.isfile(filename)),
            str(os.path.isdir(filename)),
            str(os.path.islink(filename)),
        )
    )
    logging.debug("trying to find a unique file starting with the same characters ...")

    path = os.path.dirname(filename)
    if len(path) < 1:
        path = os.getcwd()

    # get existing filenames of the directory of filename:
    existingfilenames = []
    for dirpath, dirnames, filenames in os.walk(path):
        existingfilenames.extend(filenames)
        break

    # reduce filename one character by character from the end and see if any
    # existing filename starts with this substring:
    matchingfilenames = []
    # Start with the whole filename to match cases where filename is a complete substring.
    filenamesubstring = filename
    for i in range(len(filename)):
        for existingfilename in existingfilenames:
            # logging.debug('Checking substring [%s] with existing filename [%s]' % (filenamesubstring, existingfilename))
            if existingfilename.startswith(filenamesubstring):
                matchingfilenames.append(existingfilename)
        if matchingfilenames:
            logging.debug(
                "For substring [%s] I found existing filenames: %s"
                % (filenamesubstring, str(matchingfilenames))
            )
            if len(matchingfilenames) > 1:
                logging.debug(
                    "Can not use an alternative filename since it is not unique"
                )
            break
        filenamesubstring = filename[
            : -(i + 1)
        ]  # get rid of the last character of filename, one by one

    # see if the list of matchingfilenames is unique (contains one entry)
    if len(matchingfilenames) == 1:
        return matchingfilenames[0]
    else:
        return False


def is_nonbroken_link(filename):
    """
    Returns true if the filename is a non-broken symbolic link or a non-broken Windows LNK file
    and not just an ordinary file. False, for any other case like no file at all.

    @param filename: an unicode string containing a file name
    @param return: boolean
    """

    if IS_WINDOWS:
        # do lnk-files instead of symlinks:
        if is_lnk_file(filename):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(filename)
            lnk_destination = shortcut.Targetpath
            # FIXXME: check if link destination is another lnk file or not
            if os.path.exists(lnk_destination):
                return True
            else:
                return False
        else:
            return False  # file is not a windows lnk file at all

    elif os.path.isfile(filename):
        if os.path.islink(filename):
            return True
    else:
        return False


def get_link_source_file(filename):
    """
    Return a string representing the path to which the symbolic link
    or Windows LNK file points.

    @param filename: an unicode string containing a file name
    @param return: file path string (or False if broken link)
    """

    if IS_WINDOWS:
        assert is_lnk_file(filename)
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(filename)
        original_file = shortcut.Targetpath
        assert len(shortcut.Targetpath) > 0  # only continue if it is a lnk file
        if os.path.exists(original_file):
            logging.debug(
                "get_link_source_file("
                + filename
                + ") == "
                + original_file
                + "  which does exist -> non-broken link"
            )
            return original_file
        else:
            logging.debug(
                "get_link_source_file("
                + filename
                + ") == "
                + original_file
                + "  which does NOT exist -> broken link"
            )
            return False

    else:
        assert os.path.islink(filename)
        return os.readlink(filename)


def is_broken_link(filename):
    """
    This function determines if the given filename points to a file that is a broken
    symbolic link or broken Windows LNK file.
    It returns False for any other cases such as non existing files and so forth.

    @param filename: an unicode string containing a file name
    @param return: boolean
    """

    if IS_WINDOWS:
        if is_lnk_file(filename):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(filename)
            original_file = shortcut.Targetpath
            assert (
                len(shortcut.Targetpath) > 0
            )  # only continue if it is a valid lnk file

            if os.path.exists(original_file):
                logging.debug(
                    "is_broken_link("
                    + filename
                    + ") == "
                    + original_file
                    + "  which does exist -> non-broken link"
                )
                return False
            else:
                logging.debug(
                    "is_broken_link("
                    + filename
                    + ") == "
                    + original_file
                    + "  which does NOT exist -> broken link"
                )
                return True
        else:
            logging.debug(
                "is_broken_link("
                + filename
                + ")  is not a lnk file at all; thus: not a broken link"
            )
            return False

    else:
        if os.path.isfile(filename) or os.path.isdir(filename):
            return False

        try:
            return not os.path.exists(os.readlink(filename))
        except FileNotFoundError:
            return False


def is_lnk_file(filename):
    """
    This function determines whether or not the given filename is a Windows
    LNK file.

    Note: Do not add a check for the content. This method is also used for
    checking file names that do not exist yet.

    @param filename: an unicode string containing a file name
    @param return: boolean
    """

    return filename.upper().endswith(".LNK")


def split_up_filename(filename, exception_on_file_not_found=False):
    """
    Returns separate strings for the given filename.

    If filename is not a Windows lnk file, the "basename
    without the optional .lnk extension" is the same as
    the basename.

    @param filename: an unicode string containing a file name
    @param return: filename with absolute path, pathname,
        basename, basename without the optional ".lnk" extension
    """

    if not os.path.exists(filename):
        # This does make sense for splitting up filenames that are about to be created for example:
        if exception_on_file_not_found:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        else:
            logging.debug(
                "split_up_filename("
                + filename
                + ") does NOT exist. Playing along and returning non-existent filename parts."
            )
            dirname = os.path.dirname(filename)
    else:
        dirname = os.path.dirname(os.path.abspath(filename))

    basename = os.path.basename(filename)

    if is_lnk_file(basename):
        basename_without_lnk = basename[:-4]
    else:
        basename_without_lnk = basename

    return os.path.join(dirname, basename), dirname, basename, basename_without_lnk


def create_link(source, destination, options: CliOptions):
    """On non-Windows systems, a symbolic link is created that links
    source (existing file) to destination (the new symlink). On
    Windows systems a lnk-file is created instead.

    The reason why we have to use really poor performing error-prone
    "lnk"-files instead of symlinks on Windows is that you're required
    to have administration permission so that "SeCreateSymbolicLinkPrivilege"
    is granted. Sorry for this lousy operating system.
    See: https://docs.python.org/3/library/os.html#os.symlink for details about that.

    This is the reason why the "--tagrees" option does perform really bad
    on Windows. And "really bad" means factor 10 to 1000. I measured it.

    The command link option "--hardlinks" switches to hardlinks. This
    is ignored on Windows systems.

    If the destination file exists, an error is shown unless the --overwrite
    option is used which results in deleting the old file and replacing with
    the new link.

    @param source: a file name of the source, an existing file
    @param destination: a file name for the link which is about to be created

    """

    logging.debug("create_link(" + source + ", " + destination + ") called")

    if os.path.exists(destination):
        if options.overwrite:
            logging.debug(
                "destination exists and overwrite flag set → deleting old file"
            )
            os.remove(destination)
        else:
            logging.debug(
                "destination exists and overwrite flag is not set → report error to user"
            )
            error_exit(
                21,
                "Trying to create new link but found an old file with same name. "
                + 'If you want me to overwrite older files, use the "--overwrite" option. Culprit: '
                + destination,
            )

    if IS_WINDOWS:
        # do lnk-files instead of symlinks:
        shell = win32com.client.Dispatch("WScript.Shell")
        if is_lnk_file(destination):
            # prevent multiple '.lnk' extensions from happening
            # FIX: I'm not sure whether or not multiple '.lnk'
            # extensions are a valid use-case: check!
            shortcut = shell.CreateShortCut(destination)
        else:
            shortcut = shell.CreateShortCut(destination + ".lnk")
        shortcut.Targetpath = source
        shortcut.WorkingDirectory = os.path.dirname(destination)
        # shortcut.IconLocation: is derived from the source file
        shortcut.save()

    else:
        # for normal operating systems:
        if options.hardlinks:
            try:
                # use good old high-performing hard links:
                os.link(source, destination)
            except OSError:
                logging.warning(
                    "Due to cross-device links, I had to use a symbolic link as a fall-back for: "
                    + source
                )
                os.symlink(source, destination)
        else:
            # use good old high-performing symbolic links:
            os.symlink(source, destination)


def all_files_are_links_to_same_directory(files):
    """
    This function returns True when: all files in "files" are links with same
    filenames in one single directory to a matching set of original filenames in a
    different directory.

    Returns False for any other case

    @param files: list of files
    @param return: boolean
    """

    if files and is_nonbroken_link(files[0]):
        # first_link_file_components = split_up_filename(files[0])
        first_original_file_components = split_up_filename(
            get_link_source_file(files[0])
        )
    else:
        return False

    for current_file in files:
        if current_file is not str:
            logging.info("not str")
            return False
        if not os.path.exists(current_file):
            logging.info("not path exists")
            return False
        current_link_components = split_up_filename(
            current_file
        )  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
        current_original_components = split_up_filename(
            get_link_source_file(current_file)
        )
        if (
            current_original_components[1] != first_original_file_components[1]
            or current_link_components[2] != current_original_components[2]
        ):
            logging.info("non matching")
            return False
    return True


# REFACTOR: abstract tags functionality.
def handle_file_and_optional_link(
    orig_filename, tags, do_remove, do_filter, dryrun, options: CliOptions
):
    """
    @param orig_filename: string containing one file name
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: number of errors and optional new filename
    """

    num_errors = 0
    original_dir = os.getcwd()
    logging.debug(
        'handle_file_and_optional_link("' + orig_filename + '") …  ' + "★" * 20
    )
    logging.debug("handle_file_and_optional_link: original directory = " + original_dir)

    if os.path.isdir(orig_filename):
        logging.warning(
            'Skipping directory "%s" because this tool only renames file names.'
            % orig_filename
        )
        return num_errors, False

    filename, dirname, basename, basename_without_lnk = split_up_filename(orig_filename)
    global list_of_link_directories

    if not (os.path.isfile(filename) or os.path.islink(filename)):
        logging.debug(
            "handle_file_and_optional_link: this is no regular file nor a link; "
            + "looking for an alternative file that starts with same substring …"
        )

        # try to find unique alternative file:
        alternative_filename = find_unique_alternative_to_file(filename)

        if not alternative_filename:
            logging.debug(
                "handle_file_and_optional_link: Could not locate alternative "
                + "basename that starts with same substring"
            )
            logging.error(
                'Skipping "%s" because this tool only renames existing file names.'
                % filename
            )
            num_errors += 1
            return num_errors, False
        else:
            logging.info(
                'Could not find basename "%s" but found "%s" instead which starts with same substring ...'
                % (filename, alternative_filename)
            )
            filename, dirname, basename, basename_without_lnk = split_up_filename(
                alternative_filename
            )

    if dirname and os.getcwd() != dirname:
        logging.debug('handle_file_and_optional_link: changing to dir "%s"' % dirname)
        os.chdir(dirname)
    # else:
    #     logging.debug("handle_file_and_optional_link: no dirname found or os.getcwd() is dirname")

    # if basename is a link and has same basename, tag the source file as well:
    if TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS and is_nonbroken_link(filename):
        logging.debug(
            "handle_file_and_optional_link: file is a non-broken link (and "
            + "TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS is set)"
        )

        (
            old_source_filename,
            old_source_dirname,
            old_source_basename,
            old_source_basename_without_lnk,
        ) = split_up_filename(get_link_source_file(filename))

        linkbasename_same_as_originalbasename = False
        if is_lnk_file(basename):
            linkbasename_same_as_originalbasename = (
                old_source_basename == basename[:-4]
            )  # remove ending '.lnk'
        else:
            linkbasename_same_as_originalbasename = old_source_basename == basename

        if linkbasename_same_as_originalbasename:
            logging.debug(
                'handle_file_and_optional_link: link "'
                + filename
                + '" has same basename as its source file "'
                + old_source_filename
                + '"  '
                + "v" * 20
            )

            logging.debug(
                'handle_file_and_optional_link: invoking handle_file_and_optional_link("'
                + old_source_filename
                + '")  '
                + "v" * 20
            )
            additional_errors, new_source_basename = handle_file_and_optional_link(
                old_source_filename, tags, do_remove, do_filter, dryrun
            )
            num_errors += additional_errors
            logging.debug(
                'handle_file_and_optional_link: RETURNED handle_file_and_optional_link("'
                + old_source_filename
                + '")  '
                + "v" * 20
            )

            # FIX: 2018-06-02: introduced to debug https://github.com/novoid/filetags/issues/22
            logging.debug("old_source_dirname: [" + old_source_dirname + "]")
            logging.debug("new_source_basename: [" + new_source_basename + "]")

            new_source_filename = os.path.join(old_source_dirname, new_source_basename)
            (
                new_source_filename,
                new_source_dirname,
                new_source_basename,
                new_source_basename_without_lnk,
            ) = split_up_filename(new_source_filename)

            if old_source_basename != new_source_basename:
                logging.debug(
                    'handle_file_and_optional_link: Tagging the symlink-destination file of "'
                    + basename
                    + '" ("'
                    + old_source_filename
                    + '") as well …'
                )

                if options.dryrun:
                    logging.debug(
                        'handle_file_and_optional_link: I would re-link the old sourcefilename "'
                        + old_source_filename
                        + '" to the new one "'
                        + new_source_filename
                        + '"'
                    )
                else:
                    new_filename = os.path.join(
                        dirname, new_source_basename_without_lnk
                    )
                    logging.debug(
                        'handle_file_and_optional_link: re-linking link "'
                        + new_filename
                        + '" from the old sourcefilename "'
                        + old_source_filename
                        + '" to the new one "'
                        + new_source_filename
                        + '"'
                    )
                    os.remove(filename)
                    create_link(new_source_filename, new_filename, options=options)
                # we've already handled the link source and created the updated link, return now without calling handle_file once more ...
                os.chdir(
                    dirname
                )  # go back to original dir after handling links of different directories
                return num_errors, new_filename
            else:
                logging.debug(
                    'handle_file_and_optional_link: The old sourcefilename "'
                    + old_source_filename
                    + "\" did not change. So therefore I don't re-link."
                )
                # we've already handled the link source and created the updated link, return now without calling handle_file once more ...
                os.chdir(
                    dirname
                )  # go back to original dir after handling links of different directories
                return num_errors, old_source_filename
        else:
            logging.debug(
                'handle_file_and_optional_link: The file "'
                + filename
                + '" is a link to "'
                + old_source_filename
                + '" but they two do have different basenames. Therefore I ignore the original file.'
            )
        os.chdir(
            dirname
        )  # go back to original dir after handling links of different directories
    else:
        logging.debug(
            "handle_file_and_optional_link: file is not a non-broken link ("
            + repr(is_nonbroken_link(basename))
            + ") or TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS is not set"
        )

    logging.debug(
        "handle_file_and_optional_link: after handling potential link originals, I now handle "
        + "the file we were talking about in the first place: "
        + filename
    )

    new_filename = handle_file(filename, tags, do_remove, do_filter, dryrun, options)

    logging.debug(
        "handle_file_and_optional_link: switching back to original directory = "
        + original_dir
    )
    os.chdir(original_dir)  # reset working directory
    logging.debug(
        'handle_file_and_optional_link("' + orig_filename + '") FINISHED  ' + "★" * 20
    )
    return num_errors, new_filename


# # File opertaions.
def locate_file_in_cwd_and_parent_directories(startfile, filename):
    """This method looks for the filename in the folder of startfile and its
    parent folders. It returns the file name of the first file name found.

    @param startfile: file whose path is the starting point; if False, the working path is taken
    @param filename: string of file name to look for
    @param return: file name found
    """

    logging.debug(
        'locate_file_in_cwd_and_parent_directories: called with startfile "%s" and filename "%s" ..'
        % (startfile, filename)
    )

    original_dir = os.getcwd()
    filename_in_startfile_dir = os.path.join(
        os.path.dirname(os.path.abspath(startfile)), filename
    )
    filename_in_startdir = os.path.join(startfile, filename)
    if (
        startfile
        and os.path.isfile(startfile)
        and os.path.isfile(filename_in_startfile_dir)
    ):
        # startfile=file: try to find the file within the dir where startfile lies:
        logging.debug(
            'locate_file_in_cwd_and_parent_directories: found "%s" in directory of "%s" ..'
            % (
                os.path.basename(filename_in_startfile_dir),
                os.path.dirname(filename_in_startfile_dir),
            )
        )
        return filename_in_startfile_dir
    elif (
        startfile and os.path.isdir(startfile) and os.path.isfile(filename_in_startdir)
    ):
        # startfile=dir: try to find the file within the startfile dir:
        logging.debug(
            'locate_file_in_cwd_and_parent_directories: found "%s" in directory "%s" ...'
            % (os.path.basename(filename_in_startdir), startfile)
        )
        return filename_in_startdir
    else:
        # no luck with the first guesses, trying to locate the file by traversing the parent directories:
        if os.path.isfile(startfile):
            # startfile=file: set starting_dir to it dirname:
            starting_dir = os.path.dirname(os.path.abspath(startfile))
            logging.debug(
                "locate_file_in_cwd_and_parent_directories: startfile [%s] found, using it as starting_dir [%s] ...."
                % (str(startfile), starting_dir)
            )
        elif os.path.isdir(startfile):
            # startfile=dir: set starting_dir to it:
            starting_dir = startfile
            logging.debug(
                "locate_file_in_cwd_and_parent_directories: startfile [%s] is a directory, using it as starting_dir [%s] ....."
                % (str(startfile), starting_dir)
            )
        else:
            # startfile is no dir nor file: using cwd as a fall-back:
            starting_dir = os.getcwd()
            logging.debug(
                "locate_file_in_cwd_and_parent_directories: no startfile found; using cwd as starting_dir [%s] ......"
                % (starting_dir)
            )

        parent_dir = os.path.abspath(os.path.join(starting_dir, os.pardir))
        logging.debug(
            'locate_file_in_cwd_and_parent_directories: looking for "%s" in directory "%s" .......'
            % (filename, parent_dir)
        )

        while parent_dir != os.getcwd():
            os.chdir(parent_dir)
            filename_to_look_for = os.path.abspath(os.path.join(os.getcwd(), filename))
            if os.path.isfile(filename_to_look_for):
                logging.debug(
                    'locate_file_in_cwd_and_parent_directories: found "%s" in directory "%s" ........'
                    % (filename, parent_dir)
                )
                os.chdir(original_dir)
                return filename_to_look_for
            parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

        os.chdir(original_dir)
        logging.debug(
            'locate_file_in_cwd_and_parent_directories: did NOT find "%s" in current directory or any parent directory'
            % filename
        )
        return False


# REFACTOR: Narrow down the options.
def get_files_of_directory(directory, options: CliOptions):
    """
    Lists the files of the given directory and returns a list of its files.

    @param directory: string of an existing directory
    @param return: list of file names of given directory
    """

    files = []
    logging.debug(
        "get_files_of_directory("
        + directory
        + ") called and traversing file system ..."
    )
    for dirpath, dirnames, filenames in os.walk(directory):
        if len(files) % 5000 == 0 and len(files) > 0:
            # While debugging a large hierarchy scan, I'd like to print
            # out some stuff in-between scanning
            logging.info("found " + str(len(files)) + " files so far ... counting ...")
        if options.recursive:
            files.extend([os.path.join(dirpath, x) for x in filenames])
        else:
            files.extend(filenames)
            break
    logging.debug(
        "get_files_of_directory("
        + directory
        + ") finished with "
        + str(len(files))
        + " items"
    )

    return files


# REFACTOR: Narrow down the options.
def assert_empty_tagfilter_directory(directory, options: CliOptions):
    """
    Creates non-existent tagfilter directory or deletes and re-creates it.

    @param directory: the directory to use as starting directory
    """

    if (
        options.tagtrees_directory
        and os.path.isdir(directory)
        and os.listdir(directory)
        and not options.overwrite
    ):
        error_exit(
            13,
            "The given tagtrees directory "
            + directory
            + " is not empty. Aborting here instead "
            + "of removing its content without asking. Please free it up yourself and try again.",
        )

    if not os.path.isdir(directory):
        logging.debug(
            'creating non-existent tagfilter directory "%s" ...' % str(directory)
        )
        if not options.dryrun:
            os.makedirs(directory)
    else:
        # FIX: 2018-04-04: I guess this is never reached because this script
        # does never rm -r on that directory: check it and add overwrite parameter
        logging.debug(
            'found old tagfilter directory "%s"; deleting directory ...'
            % str(directory)
        )
        if not options.dryrun:
            import shutil  # for removing directories with shutil.rmtree()

            shutil.rmtree(directory)
            logging.debug('re-creating tagfilter directory "%s" ...' % str(directory))
            os.makedirs(directory)
    if not options.dryrun:
        assert os.path.isdir(directory)


# REFACTOR: abstract tags functionality.
def handle_file(orig_filename, tags, do_remove, do_filter, dryrun, options: CliOptions):
    """
    @param orig_filename: string containing one file name with absolute path
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value or new filename
    """

    assert orig_filename.__class__ == str
    assert tags.__class__ == list
    if do_remove:
        assert do_remove.__class__ == bool
    if do_filter:
        assert do_filter.__class__ == bool
    if dryrun:
        assert dryrun.__class__ == bool

    global chosen_tagtrees_dir

    filename, dirname, basename, basename_without_lnk = split_up_filename(
        orig_filename, exception_on_file_not_found=True
    )

    logging.debug(
        'handle_file("'
        + filename
        + '") '
        + "#" * 10
        + '  … with working dir "'
        + os.getcwd()
        + '"'
    )

    if do_filter:
        print_item_transition(dirname, basename, chosen_tagtrees_dir, transition="link")
        if not dryrun:
            create_link(filename, os.path.join(chosen_tagtrees_dir, basename), options=options)

    else:  # add or remove tags:
        new_basename = basename
        logging.debug(
            "handle_file: set new_basename ["
            + new_basename
            + "] according to parameters (initialization)"
        )

        for tagname in tags:
            if tagname.strip() == "":
                continue
            if do_remove:
                new_basename = removing_tag_from_filename(new_basename, tagname)
                logging.debug(
                    "handle_file: set new_basename ["
                    + new_basename
                    + "] when do_remove"
                )
            elif tagname[0] == "-":
                new_basename = removing_tag_from_filename(new_basename, tagname[1:])
                logging.debug(
                    "handle_file: set new_basename ["
                    + new_basename
                    + "] when tag starts with a minus"
                )
            else:
                # FIXXME: not performance optimized for large number of unique tags in many lists:
                tag_in_unique_tags, matching_unique_tag_list = (
                    item_contained_in_list_of_lists(tagname, unique_tags)
                )

                if tagname != tag_in_unique_tags:
                    new_basename = adding_tag_to_filename(new_basename, tagname)
                    logging.debug(
                        "handle_file: set new_basename ["
                        + new_basename
                        + "] when tagname != tag_in_unique_tags"
                    )
                else:
                    # if tag within unique_tags found, and new unique tag is given, remove old tag:
                    # e.g.: unique_tags = (u'yes', u'no') -> if 'no' should be added, remove existing tag 'yes' (and vice versa)
                    # If user enters contradicting tags, only the last one will be applied.
                    # FIXXME: this is an undocumented feature -> please add proper documentation

                    current_filename_tags = extract_tags_from_filename(new_basename)
                    conflicting_tags = list(
                        set(current_filename_tags).intersection(
                            matching_unique_tag_list
                        )
                    )
                    logging.debug(
                        "handle_file: found unique tag %s which require old unique tag(s) to be removed: %s"
                        % (tagname, repr(conflicting_tags))
                    )
                    for conflicting_tag in conflicting_tags:
                        new_basename = removing_tag_from_filename(
                            new_basename, conflicting_tag
                        )
                        logging.debug(
                            "handle_file: set new_basename ["
                            + new_basename
                            + "] when conflicting_tag in conflicting_tags"
                        )
                    new_basename = adding_tag_to_filename(new_basename, tagname)
                    logging.debug(
                        "handle_file: set new_basename ["
                        + new_basename
                        + "] after adding_tag_to_filename()"
                    )

        new_filename = os.path.join(dirname, new_basename)

        if do_remove:
            transition = "delete"
        else:
            transition = "add"

        if basename != new_basename:

            list_of_link_directories.append(dirname)

            if len(list_of_link_directories) > 1:
                logging.debug(
                    "new_filename is a symlink. Screen output of transistion gets postponed to later on."
                )
            # REFACTOR: Change options to a function parameter.
            elif not options.quiet:
                print_item_transition(
                    dirname, basename, new_basename, transition=transition
                )

            if not dryrun:
                os.rename(filename, new_filename)

        logging.debug('handle_file("' + filename + '") ' + "#" * 10 + "  finished")
        return new_filename
