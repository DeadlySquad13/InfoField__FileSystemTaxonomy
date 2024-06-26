import logging
import os

from filetags.cli import ask_for_tags
from filetags.cli.parser.options import CliOptions
from filetags.cli.preprocessing import \
    get_upto_nine_keys_of_dict_with_highest_value
from filetags.common.types import Filenames, TagnamesVocabulary, Vocabulary
from filetags.consts import TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS
from filetags.file_operations import (all_files_are_links_to_same_directory,
                                      get_link_source_file, is_nonbroken_link,
                                      split_up_filename)
from filetags.tags.VirtualTagsProtocol import VirtualTagsProtocol
from filetags.utils.logging import error_exit


def handle_remove(
    virtualTags: VirtualTagsProtocol,
    files: Filenames,
    tags_for_vocabulary: TagnamesVocabulary,
):
    # vocabulary for completing tags is current tags of files
    for currentfile in files:
        # add tags so that list contains all unique tags:
        for newtag in virtualTags.current_servic.extract_tags_from_filename(
            currentfile
        ):
            virtualTags.add_tag_to_countdict(newtag, tags_for_vocabulary)
    vocabulary = sorted(tags_for_vocabulary.keys())
    upto9_tags_for_shortcuts = sorted(
        get_upto_nine_keys_of_dict_with_highest_value(
            tags_for_vocabulary, omit_filetags_donotsuggest_tags=True
        )
    )

    return vocabulary, upto9_tags_for_shortcuts


def handle_tag_filtering(
    virtualTags: VirtualTagsProtocol,
    tags_for_vocabulary: TagnamesVocabulary,
    options: CliOptions = {},
):
    for tag in virtualTags.current_service.get_tags_from_files_and_subfolders(
        startdir=os.getcwd(), options=options
    ):
        virtualTags.add_tag_to_countdict(tag, tags_for_vocabulary)

    logging.debug("generating vocabulary ...")
    vocabulary = sorted(tags_for_vocabulary.keys())
    upto9_tags_for_shortcuts = sorted(
        get_upto_nine_keys_of_dict_with_highest_value(
            tags_for_vocabulary, omit_filetags_donotsuggest_tags=True
        )
    )

    return vocabulary, upto9_tags_for_shortcuts


def handle_tagging(
    virtualTags: VirtualTagsProtocol,
    files: Filenames,
    vocabulary: Vocabulary,
    options: CliOptions = {},
):
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
    tags_intersection_of_files = virtualTags.get_common_tags_from_files(files)
    tags_for_visual = tags_intersection_of_files
    logging.debug(
        "found common tags: tags_intersection_of_files[%s]"
        % "], [".join(tags_intersection_of_files)
    )

    # Append current filetags with a prepended '-' in order
    # to allow tag completion for removing tags via '-tagname'
    tags_from_filenames = set()
    for currentfile in files:
        tags_from_filenames = tags_from_filenames.union(
            set(virtualTags.current_service.extract_tags_from_filename(currentfile))
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
            virtualTags.current_service.get_tags_from_files_and_subfolders(
                startdir=os.path.dirname(os.path.abspath(os.path.basename(files[0]))),
                options=options,
            ),
            tags_intersection_of_files,
            omit_filetags_donotsuggest_tags=True,
        )
    )
    logging.debug("derived upto9_tags_for_shortcuts")

    return vocabulary, upto9_tags_for_shortcuts, tags_for_visual


def handle_interactive_mode(
    virtualTags: VirtualTagsProtocol,
    files: Filenames,
    vocabulary: Vocabulary,
    options: CliOptions = {},
):
    tags_for_visual = None

    if len(options.files) < 1 and not options.tagfilter:
        error_exit(5, "Please add at least one file name as argument")

    tags_for_vocabulary = {}
    upto9_tags_for_shortcuts = []

    # look out for .filetags file and add readline support for tag completion if found with content
    if options.remove:
        vocabulary, upto9_tags_for_shortcuts = handle_remove(
            virtualTags, files, tags_for_vocabulary=tags_for_vocabulary
        )
    elif options.tagfilter:
        vocabulary, upto9_tags_for_shortcuts = handle_tag_filtering(
            virtualTags, tags_for_vocabulary=tags_for_vocabulary
        )
    else:
        vocabulary, upto9_tags_for_shortcuts, tags_for_visual = handle_tagging(
            virtualTags, files, vocabulary=vocabulary
        )

    logging.debug(
        "derived vocabulary with %i entries" % len(vocabulary)
    )  # using default vocabulary which was generate above

    # ==================== Interactive asking user for tags ============================= ##
    tags_from_userinput = ask_for_tags(
        virtualTags,
        vocabulary,
        upto9_tags_for_shortcuts,
        tags_for_visual,
        options=options,
    )
    # ==================== Interactive asking user for tags ============================= ##
    print("")  # new line after input for separating input from output

    return tags_from_userinput
