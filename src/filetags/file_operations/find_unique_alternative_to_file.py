# import win32com
import logging
import os


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
