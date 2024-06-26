import logging
import time

from filetags.cli.parser.options import CliOptions
from filetags.consts import DEFAULT_TAGTREES_MAXDEPTH, TAGFILTER_DIRECTORY
from filetags.integrations import start_filebrowser
from filetags.tags.VirtualTagsProtocol import VirtualTagsProtocol
from filetags.utils.successful_exit import successful_exit


def handle_tagtrees_generation(
    virtualTags: VirtualTagsProtocol, filtertags=None, options: CliOptions = {}
):
    """
    Handles the options and preprocessing for generating tagtrees.

    @param: filtertags: (list) if options.tagfilter is used,
    this list contains the user-entered list of tags to filter for
    """

    logging.debug("handling option for tagtrees")

    # The command line options for tagtrees_handle_no_tag is checked:
    ignore_nontagged = False
    nontagged_subdir = False
    if options.tagtrees_handle_no_tag:
        if options.tagtrees_handle_no_tag[0] == "treeroot":
            logging.debug("options.tagtrees_handle_no_tag found: treeroot (default)")
            pass  # keep defaults
        elif options.tagtrees_handle_no_tag[0] == "ignore":
            logging.debug("options.tagtrees_handle_no_tag found: ignore")
            ignore_nontagged = True
        else:
            ignore_nontagged = False
            nontagged_subdir = options.tagtrees_handle_no_tag[0]
            logging.debug(
                "options.tagtrees_handle_no_tag found: use foldername ["
                + repr(options.tagtrees_handle_no_tag)
                + "]"
            )

    chosen_maxdepth = DEFAULT_TAGTREES_MAXDEPTH
    if options.tagtrees_depth:
        chosen_maxdepth = options.tagtrees_depth[0]
        logging.debug(
            "User overrides the default tagtrees depth to: " + str(chosen_maxdepth)
        )
        if chosen_maxdepth > 4:
            logging.warning(
                "The chosen tagtrees depth of "
                + str(chosen_maxdepth)
                + " is rather high."
            )
            logging.warning(
                "When linking more than a few files, this "
                + "might take a long time using many filesystem inodes."
            )

    # FIX: 2018-04-04: following 4-lines block re-occurs for options.tagfilter: unify accordingly!
    chosen_tagtrees_dir = TAGFILTER_DIRECTORY
    if options.tagtrees_directory:
        chosen_tagtrees_dir = options.tagtrees_directory[0]
        logging.debug(
            "User overrides the default tagtrees directory to: "
            + str(chosen_tagtrees_dir)
        )

    start = time.time()
    virtualTags.generate_tagtrees(
        chosen_tagtrees_dir,
        chosen_maxdepth,
        ignore_nontagged,
        nontagged_subdir,
        options.tagtrees_link_missing_mutual_tagged_items,
        filtertags,
    )
    delta = time.time() - start  # it's a float
    if delta > 3:
        logging.info("Generated tagtrees in %.2f seconds" % delta)
    if not options.quiet:
        start_filebrowser(chosen_tagtrees_dir)
    successful_exit()
