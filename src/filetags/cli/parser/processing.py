"""
Process cli arguments for easier use in program:
    assign defaults, format them, change to established strutures, etc...
"""

import logging

from filetags.cli.parser.options import CliOptions
from filetags.common.types import Path
from filetags.consts import BETWEEN_TAG_SEPARATOR, TAGFILTER_DIRECTORY


def extract_tags_from_argument(argument):
    """
    @param argument: string containing one or more tags
    @param return: a list of unicode tags
    """

    assert argument.__class__ == str

    if len(argument) > 0:
        # REFACTOR: Move split functionality to `Tags`.
        return argument.split(str(BETWEEN_TAG_SEPARATOR))
    else:
        return False


def extract_filenames_from_argument(argument):
    """
    @param argument: string containing one or more file names
    @param return: a list of unicode file names
    """

    # TODO: currently works without need to convertion but add check later on
    return argument


# Holds the definitive choice for a destination folder for filtering or tagtrees.
def get_chosen_tagtrees_dir(options: CliOptions = {}) -> Path:
    if not options.tagtrees_directory:
        return TAGFILTER_DIRECTORY

    chosen_tagtrees_dir = str(options.tagtrees_directory[0])
    logging.debug(
        "User overrides the default tagtrees directory to: "
        + chosen_tagtrees_dir
    )

    return chosen_tagtrees_dir
