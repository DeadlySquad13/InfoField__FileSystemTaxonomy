# import win32com
import errno
import logging
import os

from filetags.cli.parser import CliOptions
from filetags.consts import IS_WINDOWS


# REFACTOR: Move out of it. Maybe change to pathlib and remove entirely.
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
