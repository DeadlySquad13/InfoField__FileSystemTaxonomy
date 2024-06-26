# import win32com
import logging
import os

from filetags.cli.parser import CliOptions
from filetags.utils.logging import error_exit


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
def get_files_of_directory(directory, options: CliOptions = {}):
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
# STYLE: Change naming to abstract from tagfilter directory.
def assert_empty_tagfilter_directory(directory, options: CliOptions = {}):
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
