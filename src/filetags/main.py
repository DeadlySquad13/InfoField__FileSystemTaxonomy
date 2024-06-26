import logging
import os
import pathlib
import sys

from filetags.cli import TTY_HEIGHT, TTY_WIDTH
from filetags.cli.parser import (extract_filenames_from_argument,
                                 extract_tags_from_argument, validate_options)
from filetags.cli.preprocessing import locate_and_parse_controlled_vocabulary
from filetags.consts import (BETWEEN_TAG_SEPARATOR, IS_WINDOWS,
                             PROG_VERSION_DATE)
from filetags.file_operations import (assert_empty_tagfilter_directory,
                                      get_files_of_directory)
from filetags.scenarios import process_files
from filetags.scenarios.interactive import handle_interactive_mode
from filetags.tag_gardening import handle_tag_gardening
from filetags.tags import (filter_files_matching_tags,
                           get_tags_from_files_and_subfolders,
                           list_unknown_tags, print_tag_dict)
from filetags.Tagtree import handle_option_tagtrees
from filetags.utils.logging import error_exit, handle_logging
from filetags.utils.successful_exit import successful_exit

# import clint  # for config file handling


# TODO:
# - fix parts marked with «FIXXME»
# - move global variables to parameter lists, avoiding global variables in general
# - $HOME/.config/ with default options (e.g., geeqie)
#   - using clint/resource
#   - if not found, write default config with defaults (and comments)
# - tagfilter: --copy :: copy files instead of creating symlinks
# - tagfilter: all toggle-cmd line args as special tags: --copy and so forth
#   - e.g., when user enters tag "--copy" when interactively reading tags,
#       handle it like options.copy
#   - overwriting cmd-line arguments (if contradictory)
#   - allow combination of cmd-line tags and interactive tags
#     - they get combined
# - tagfilter: additional parameter to move matching files to a temporary subfolder
#   - renaming/deleting of symlinks does not modify original files
# - tagfilter: --notags :: do not ask for tags, use all items that got no tag
#      at all
# - tagfilter: --ignoredirs :: do not symlink/copy directories
# - tagfilter: --emptytmpdir :: empty temporary directory after the image viewer exits
# - use "open" to open first(?) file

controlled_vocabulary_filename = ""
list_of_link_directories = []
chosen_tagtrees_dir = False  # holds the definitive choice for a destination folder for filtering or tagtrees

from filetags.cli.parser import get_cli_options

options = get_cli_options()

from filetags.integrations import start_filebrowser

# REFACTOR: Type.
# dict of big list of dicts: 'filename', 'path' and other metadata
cache_of_files_with_metadata = {}


def main():
    """Main function"""

    if options.version:
        print(os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_DATE)
        sys.exit(0)

    handle_logging(options)

    validate_options(options)

    logging.debug("extracting list of files ...")
    logging.debug("len(options.files) [%s]" % str(len(options.files)))

    files = extract_filenames_from_argument(options.files)

    if IS_WINDOWS and len(files) == 1:
        # Windows CLI does not resolve wildcard globbing: https://github.com/novoid/filetags/issues/25
        # Therefore, filetags has to do the business proper(TM) operating systems usually
        # does: converting file globs to lists of files:

        # logging.debug("WINDOWS: files[0] RAW [%s]" % str(files[0]))
        path = pathlib.Path(files[0]).expanduser()
        parts = path.parts[1:] if path.is_absolute() else path.parts
        expandedfiles = pathlib.Path(path.root).glob(
            str(pathlib.Path("").joinpath(*parts))
        )
        files = []
        for file in expandedfiles:
            # logging.debug("WINDOWS: file within expandedfiles [%s]" % str(file))
            files.append(str(file))
        logging.debug("WINDOWS: len(files) [%s]" % str(len(files)))
        logging.debug("WINDOWS: files CONVERTED [%s]" % str(files))

    global list_of_link_directories
    global chosen_tagtrees_dir

    logging.debug("%s filenames found: [%s]" % (str(len(files)), "], [".join(files)))
    logging.debug(
        "reported console width: "
        + str(TTY_WIDTH)
        + " and height: "
        + str(TTY_HEIGHT)
        + "   (80/80 is the fall-back)"
    )
    tags_from_userinput = []
    # QUESTION: Why false?
    vocabulary = sorted(
        locate_and_parse_controlled_vocabulary(files and files[0] or False)
    )

    if len(options.files) < 1 and not (
        options.tagtrees
        or options.tagfilter
        or options.list_tags_by_alphabet
        or options.list_tags_by_number
        or options.list_unknown_tags
        or options.tag_gardening
    ):
        error_exit(5, "Please add at least one file name as argument")

    if (
        options.list_tags_by_alphabet
        or options.list_tags_by_number
        or options.list_unknown_tags
    ):

        tag_dict = get_tags_from_files_and_subfolders(
            startdir=os.getcwd(), options=options
        )
        if not tag_dict:
            print("\nNo file containing tags found in this folder hierarchy.\n")
            return {}

        if options.list_tags_by_alphabet:
            logging.debug("handling option list_tags_by_alphabet")
            print_tag_dict(
                tag_dict,
                vocabulary=vocabulary,
                sort_index=0,
                print_similar_vocabulary_tags=True,
            )
            successful_exit()

        elif options.list_tags_by_number:
            logging.debug("handling option list_tags_by_number")
            print_tag_dict(
                tag_dict,
                vocabulary=vocabulary,
                sort_index=1,
                print_similar_vocabulary_tags=True,
            )
            successful_exit()

        elif options.list_unknown_tags:
            logging.debug("handling option list_unknown_tags")
            list_unknown_tags(tag_dict)
            successful_exit()

    elif options.tag_gardening:
        # REFACTOR: Move to decorator this debugs and wrap each handler with
        # it.
        logging.debug("handling option for tag gardening")
        handle_tag_gardening(
            vocabulary,
            cache_of_files_with_metadata=cache_of_files_with_metadata,
            options=options,
        )
        successful_exit()

    elif options.tagtrees and not options.tagfilter:
        # STYLE: Rename to remove `option`.
        handle_option_tagtrees()

    elif options.interactive or not options.tags:
        tags_from_userinput = handle_interactive_mode(files, vocabulary=vocabulary, options=options)

    else:
        # non-interactive: extract list of tags
        logging.debug("non-interactive mode: extracting tags from argument ...")

        tags_from_userinput = extract_tags_from_argument(options.tags[0])

        if not tags_from_userinput:
            # QUESTION: can this even be the case?
            logging.info("no tags given, exiting.")
            sys.stdout.flush()
            sys.exit(0)

    # TODO: Move logging to corresponding handler.
    logging.debug("tags found: [%s]" % "], [".join(tags_from_userinput))
    if options.remove:
        logging.info(
            'removing tags "%s" ...'
            % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput))
        )
    elif options.tagfilter:
        logging.info(
            'filtering items with tag(s) "%s" and linking to directory "%s" ...'
            % (
                str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput)),
                str(chosen_tagtrees_dir),
            )
        )
    elif options.interactive:
        logging.info(
            'processing tags "%s" ...'
            % str(BETWEEN_TAG_SEPARATOR.join(tags_from_userinput))
        )

    if options.tagfilter and not files and not options.tagtrees:
        assert_empty_tagfilter_directory(chosen_tagtrees_dir, options)
        files = filter_files_matching_tags(
            get_files_of_directory(os.getcwd(), options), tags_from_userinput
        )
    elif options.tagfilter and not files and options.tagtrees:
        # the combination of tagtrees and tagfilter requires user input of tags which was done above
        handle_option_tagtrees(tags_from_userinput)

    logging.debug("iterate over files ...")

    max_file_length = 0

    for filename in files:
        if len(filename) > max_file_length:
            max_file_length = len(filename)
    logging.debug("determined maximum file name length with %i" % max_file_length)

    process_files(
        files,
        filtertags=tags_from_userinput,
        list_of_link_directories=list_of_link_directories,
        max_file_length=max_file_length,
        options=options,
    )

    if options.tagfilter and not options.quiet:
        logging.debug('Now openeing filebrowser for dir "' + chosen_tagtrees_dir + '"')
        start_filebrowser(chosen_tagtrees_dir)

    successful_exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")
