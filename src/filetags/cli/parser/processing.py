
from filetags.consts import BETWEEN_TAG_SEPARATOR


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
