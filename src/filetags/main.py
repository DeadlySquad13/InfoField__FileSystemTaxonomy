import logging
import os
import pathlib
import sys

from filetags.cli import TTY_HEIGHT, TTY_WIDTH, ask_for_tags
from filetags.cli.parser import (extract_filenames_from_argument,
                                 extract_tags_from_argument, validate_options)
from filetags.cli.preprocessing import (
    get_upto_nine_keys_of_dict_with_highest_value,
    locate_and_parse_controlled_vocabulary)
from filetags.consts import (BETWEEN_TAG_SEPARATOR, IS_WINDOWS,
                             PROG_VERSION_DATE,
                             TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS,
                             TAGFILTER_DIRECTORY)
from filetags.file_operations import (all_files_are_links_to_same_directory,
                                      assert_empty_tagfilter_directory,
                                      get_files_of_directory,
                                      get_link_source_file,
                                      handle_file_and_optional_link,
                                      is_broken_link, is_nonbroken_link,
                                      split_up_filename)
from filetags.tag_gardening import handle_tag_gardening
from filetags.tags import (add_tag_to_countdict, extract_tags_from_filename,
                           filter_files_matching_tags,
                           get_tags_from_files_and_subfolders,
                           list_unknown_tags, print_tag_dict)
from filetags.Tagtree import get_common_tags_from_files, handle_option_tagtrees
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

# QUESTION: Change to pathlib?
Files = list[str]
# TODO: Make concrete.
Tags = dict
Vocabulary = dict
TagsForShortcuts = list


def handle_remove(files: Files, tags_for_vocabulary: Tags):
    # vocabulary for completing tags is current tags of files
    for currentfile in files:
        # add tags so that list contains all unique tags:
        for newtag in extract_tags_from_filename(currentfile):
            add_tag_to_countdict(newtag, tags_for_vocabulary)
    vocabulary = sorted(tags_for_vocabulary.keys())
    upto9_tags_for_shortcuts = sorted(
        get_upto_nine_keys_of_dict_with_highest_value(
            tags_for_vocabulary, omit_filetags_donotsuggest_tags=True
        )
    )

    return vocabulary, upto9_tags_for_shortcuts


def handle_tag_filtering(tags_for_vocabulary: Tags):
    # FIX: 2018-04-04: following 4-lines block re-occurs for options.tagtrees: unify accordingly!
    chosen_tagtrees_dir = TAGFILTER_DIRECTORY
    if options.tagtrees_directory:
        chosen_tagtrees_dir = options.tagtrees_directory[0]
        logging.debug(
            "User overrides the default tagtrees directory to: "
            + str(chosen_tagtrees_dir)
        )

    for tag in get_tags_from_files_and_subfolders(
        startdir=os.getcwd(), options=options
    ):
        add_tag_to_countdict(tag, tags_for_vocabulary)

    logging.debug("generating vocabulary ...")
    vocabulary = sorted(tags_for_vocabulary.keys())
    upto9_tags_for_shortcuts = sorted(
        get_upto_nine_keys_of_dict_with_highest_value(
            tags_for_vocabulary, omit_filetags_donotsuggest_tags=True
        )
    )

    return vocabulary, upto9_tags_for_shortcuts


def handle_tagging(files: Files, vocabulary: Vocabulary):
    if not files:
        return vocabulary, []

    # If it is only one file which is a link to the same basename
    # in a different directory, show the original directory:
    if (
        len(files) == 1
        and TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS
        and is_nonbroken_link(files[0])
    ):
        link_file = split_up_filename(files[0])
        original_file = split_up_filename(
            get_link_source_file(files[0])
        )  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
        if link_file[1] != original_file[1] and link_file[2] == original_file[2]:
            # basenames are same, dirs are different
            print(
                "     ... link: tagging also matching filename in " + original_file[1]
            )
    # do the same but for a list of link files whose paths have to match:
    if (
        len(files) > 1
        and TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS
        and all_files_are_links_to_same_directory(files)
    ):
        # using first file for determining directories:
        link_file = split_up_filename(files[0])
        original_file = split_up_filename(
            get_link_source_file(files[0])
        )  # 0 = absolute path incl. filename; 1 = dir; 2 = filename
        print("     ... links: tagging also matching filenames in " + original_file[1])

    # remove given (shared) tags from the vocabulary:
    tags_intersection_of_files = get_common_tags_from_files(files)
    tags_for_visual = tags_intersection_of_files
    logging.debug(
        "found common tags: tags_intersection_of_files[%s]"
        % "], [".join(tags_intersection_of_files)
    )

    # append current filetags with a prepended '-' in order to allow tag completion for removing tags via '-tagname'
    tags_from_filenames = set()
    for currentfile in files:
        tags_from_filenames = tags_from_filenames.union(
            set(extract_tags_from_filename(currentfile))
        )
    negative_tags_from_filenames = set()
    for currenttag in list(tags_from_filenames):
        negative_tags_from_filenames.add("-" + currenttag)

    vocabulary = list(
        set(vocabulary).union(negative_tags_from_filenames)
        - set(tags_intersection_of_files)
    )

    logging.debug("deriving upto9_tags_for_shortcuts ...")
    logging.debug("files[0] = " + files[0])
    logging.debug(
        "startdir = " + os.path.dirname(os.path.abspath(os.path.basename(files[0])))
    )
    upto9_tags_for_shortcuts = sorted(
        get_upto_nine_keys_of_dict_with_highest_value(
            get_tags_from_files_and_subfolders(
                startdir=os.path.dirname(os.path.abspath(os.path.basename(files[0]))),
                options=options,
            ),
            tags_intersection_of_files,
            omit_filetags_donotsuggest_tags=True,
        )
    )
    logging.debug("derived upto9_tags_for_shortcuts")

    return vocabulary, upto9_tags_for_shortcuts, tags_for_visual


def handle_interactive_mode(files: Files, vocabulary: Vocabulary):
    tags_for_visual = None

    if len(options.files) < 1 and not options.tagfilter:
        error_exit(5, "Please add at least one file name as argument")

    tags_for_vocabulary = {}
    upto9_tags_for_shortcuts = []

    # look out for .filetags file and add readline support for tag completion if found with content
    if options.remove:
        vocabulary, upto9_tags_for_shortcuts = handle_remove(
            files, tags_for_vocabulary=tags_for_vocabulary
        )
    elif options.tagfilter:
        vocabulary, upto9_tags_for_shortcuts = handle_tag_filtering(
            tags_for_vocabulary=tags_for_vocabulary
        )
    else:
        vocabulary, upto9_tags_for_shortcuts, tags_for_visual = handle_tagging(
            files, vocabulary=vocabulary
        )

    logging.debug(
        "derived vocabulary with %i entries" % len(vocabulary)
    )  # using default vocabulary which was generate above

    # ==================== Interactive asking user for tags ============================= ##
    tags_from_userinput = ask_for_tags(
        vocabulary, upto9_tags_for_shortcuts, tags_for_visual, options=options
    )
    # ==================== Interactive asking user for tags ============================= ##
    print("")  # new line after input for separating input from output

    return tags_from_userinput


def process_files(files: Files, filtertags, list_of_link_directories):
    num_errors = 0
    for filename in files:
        if not os.path.exists(filename):
            logging.error('File "' + filename + '" does not exist. Skipping this one …')
            logging.debug("problematic filename: " + filename)
            logging.debug("os.getcwd() = " + os.getcwd())
            num_errors += 1

        elif is_broken_link(filename):
            # skip broken links completely and write error message:
            logging.error(
                'File "' + filename + '" is a broken link. Skipping this one …'
            )
            num_errors += 1

        else:
            # if filename is a link, tag the source file as well:
            handle_file_and_optional_link(
                filename,
                filtertags,
                options.remove,
                options.tagfilter,
                options.dryrun,
            )
            logging.debug("list_of_link_directories: " + repr(list_of_link_directories))

            if len(list_of_link_directories) > 1:
                logging.debug(
                    "Seems like we've found links and renamed their source "
                    + "as well. Print out the those directories as well:"
                )
                print(
                    "      This link has a link source with a matching basename. I renamed it there as well:"
                )
                for directory in list_of_link_directories[:-1]:
                    print("      · " + directory)
            list_of_link_directories = []

    if num_errors > 0:
        error_exit(
            20, str(num_errors) + " error(s) occurred. Please check messages above."
        )


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
        tags_from_userinput = handle_interactive_mode(files, vocabulary=vocabulary)

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

    global max_file_length
    for filename in files:
        if len(filename) > max_file_length:
            max_file_length = len(filename)
    logging.debug("determined maximum file name length with %i" % max_file_length)

    process_files(
        files,
        filtertags=tags_from_userinput,
        list_of_link_directories=list_of_link_directories,
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
