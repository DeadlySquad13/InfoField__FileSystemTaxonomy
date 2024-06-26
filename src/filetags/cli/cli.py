import logging
import os
import readline
import sys

import colorama

from filetags.cli.parser import CliOptions, extract_tags_from_argument
from filetags.common.consts import UNIQUE_TAG_TESTSTRINGS
from filetags.completion import SimpleCompleter
from filetags.consts import BETWEEN_TAG_SEPARATOR, IS_WINDOWS
from filetags.tags.VirtualTagsProtocol import VirtualTagsProtocol
from filetags.tags.shortcuts import check_for_possible_shortcuts_in_entered_tags, print_tag_shortcut_with_numbers

if IS_WINDOWS:
    try:
        import win32com.client
    except ImportError:
        print(
            'Could not find Python module "win32com.client".\nPlease install it, e.g., '
            + 'with "sudo pip install pypiwin32".'
        )
        sys.exit(3)
    import pathlib

TTY_HEIGHT: int
TTY_WIDTH: int

# Determining the window size of the terminal:
if IS_WINDOWS:
    TTY_HEIGHT, TTY_WIDTH = 80, 80  # fall-back values
else:
    # check to avoid stty error when stdin is not a terminal.
    if sys.stdin.isatty():
        try:
            TTY_HEIGHT, TTY_WIDTH = [
                int(x) for x in os.popen("stty size", "r").read().split()
            ]
        except ValueError:
            TTY_HEIGHT, TTY_WIDTH = 80, 80  # fall-back values
    else:
        TTY_HEIGHT, TTY_WIDTH = 80, 80

max_file_length = 0  # will be set after iterating over source files182

unique_tags = [
    UNIQUE_TAG_TESTSTRINGS
]  # list of list which contains tags that are mutually exclusive
# Note: u'teststring1' and u'teststring2' are hard-coded for testing purposes.
#       You might delete them if you don't use my unit test suite.


# # User dialog.
def ask_for_tags(
    virtualTags: VirtualTagsProtocol,
    vocabulary,
    upto9_tags_for_shortcuts,
    tags_for_visual=None,
    options: CliOptions = {},
):
    """
    Takes a vocabulary and optional up to nine tags for shortcuts and interactively asks
    the user to enter tags. Aborts program if no tags were entered. Returns list of
    entered tags.

    @param vocabulary: array containing the controlled vocabulary
    @param upto9_tags_for_shortcuts: array of tags which can be used to generate number-shortcuts
    @param return: list of up to top nine keys according to the rank of their values
    """

    completionhint = ""
    if vocabulary and len(vocabulary) > 0:

        assert vocabulary.__class__ == list

        # Register our completer function
        readline.set_completer(SimpleCompleter(vocabulary).complete)

        # Use the tab key for completion
        readline.parse_and_bind("tab: complete")

        completionhint = "; complete %s tags with TAB" % str(len(vocabulary))

    logging.debug("len(files) [%s]" % str(len(options.files)))
    logging.debug("files: %s" % str(options.files))

    print("                 ")
    print(
        "Please enter tags"
        + colorama.Style.DIM
        + ', separated by "'
        + BETWEEN_TAG_SEPARATOR
        + '"; abort with Ctrl-C'
        + completionhint
        + colorama.Style.RESET_ALL
    )
    print("                     ")
    print(virtualTags.get_tag_visual(tags_for_visual))
    print("                     ")

    if len(upto9_tags_for_shortcuts) > 0:
        print_tag_shortcut_with_numbers(
            upto9_tags_for_shortcuts,
            tags_get_added=(not options.remove and not options.tagfilter),
            tags_get_linked=options.tagfilter,
        )

    logging.debug("interactive mode: asking for tags ...")
    entered_tags = input(
        colorama.Style.DIM + "Tags: " + colorama.Style.RESET_ALL
    ).strip()
    tags_from_userinput = extract_tags_from_argument(entered_tags)

    if not tags_from_userinput:
        logging.info("no tags given, exiting.")
        sys.stdout.flush()
        sys.exit(0)
    else:
        if len(upto9_tags_for_shortcuts) > 0:
            # check if user entered number shortcuts for tags to be removed:
            tags_from_userinput = check_for_possible_shortcuts_in_entered_tags(
                tags_from_userinput, upto9_tags_for_shortcuts
            )
        return tags_from_userinput
