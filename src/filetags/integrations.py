import os
import logging
import platform

from filetags.consts import DEFAULT_IMAGE_VIEWER_LINUX, DEFAULT_IMAGE_VIEWER_WINDOWS
from filetags.cli.parser import get_cli_options

# REFACTOR: Move to functions as param.
options = get_cli_options()


def start_filebrowser(directory):
    """
    This function starts up the default file browser or the
    one given in the overriding command line parameter.

    @param directory: the directory to use as starting directory
    """

    if options.filebrowser and options.filebrowser == "none":
        logging.debug(
            'user overrides filebrowser with "none". Skipping filebrowser alltogether.'
        )
        return

    import subprocess

    current_platform = platform.system()
    logging.debug("platform.system() is: [" + current_platform + "]")
    if current_platform == "Linux":
        chosen_filebrowser = DEFAULT_IMAGE_VIEWER_LINUX
        if options.filebrowser:
            chosen_filebrowser = options.filebrowser  # override if given

        if options.dryrun:
            logging.info(
                'DRYRUN: I would now open the file browser "'
                + chosen_filebrowser
                + '" with dir "'
                + directory
                + '"'
            )
        else:
            subprocess.call([chosen_filebrowser, directory])

    elif current_platform == "Windows":
        chosen_filebrowser = DEFAULT_IMAGE_VIEWER_WINDOWS
        if options.filebrowser:
            chosen_filebrowser = options.filebrowser  # override if given

        if "\\" in directory:
            logging.debug("removing double backslashes from directory name")
            directory = directory.replace("\\\\", "\\")

        if options.dryrun:
            logging.info(
                'DRYRUN: I would now open the file browser "'
                + chosen_filebrowser
                + '" with dir "'
                + directory
                + '"'
            )
        else:
            if chosen_filebrowser == "explorer":
                os.system(r'start explorer.exe "' + directory + '"')
            else:
                logging.warning(
                    "FIXXME: for Windows, this script only supports the "
                    + "default file browser which is the file explorer."
                )

    else:
        logging.info(
            'No (default) file browser defined for platform "' + current_platform + '".'
        )
        logging.info("Please visit " + directory + " to view filtered items.")
