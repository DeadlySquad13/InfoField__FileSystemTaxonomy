import itertools  # for calculating permutations of tagtrees
import logging
import os
import time

from filetags.cli.parser import get_cli_options
from filetags.consts import (CONTROLLED_VOCABULARY_FILENAME,
                             DEFAULT_TAGTREES_MAXDEPTH, TAGFILTER_DIRECTORY)
from filetags.file_operations import (
    assert_empty_tagfilter_directory, create_link, get_files_of_directory,
    locate_file_in_cwd_and_parent_directories, split_up_filename)
from filetags.integrations import start_filebrowser
from filetags.tags import (extract_tags_from_filename,
                           filter_files_matching_tags,
                           get_tags_from_files_and_subfolders)
from filetags.utils.logging import error_exit
from filetags.utils.successful_exit import successful_exit

# REFACTOR: Move to functions as param.
options = get_cli_options()


def get_common_tags_from_files(files):
    """
    Returns a list of tags that are common (intersection) for all files.

    @param files: array of file names
    @param return: list of tags
    """

    list_of_tags_per_file = []
    for currentfile in files:
        list_of_tags_per_file.append(set(extract_tags_from_filename(currentfile)))

    return list(set.intersection(*list_of_tags_per_file))


def generate_tagtrees(
    directory,
    maxdepth,
    ignore_nontagged,
    nontagged_subdir,
    link_missing_mutual_tagged_items,
    filtertags=None,
):
    """
    This functions is somewhat sophisticated with regards to the background.
    If you're really interested in the whole story behind the
    visualization/navigation of tags using tagtrees, feel free to read [my
    PhD thesis] about it on [the tagstore webpage]. It is surely a piece of
    work I am proud of and the general chapters of it are written so that
    the average person is perfectly well able to follow.

    In short: this function takes the files of the current directory and
    generates hierarchies up to level of `$maxdepth' (by default 2) of all
    combinations of tags, [linking] all files according to their tags.

    Consider having a file like:

    ┌────
    │ My new car -- car hardware expensive.jpg
    └────

    Now you generate the tagtrees, you'll find [links] to this file within
    `~/.filetags', the default target directory: `new/' and `hardware/' and
    `expensive/' and `new/hardware/' and `new/expensive/' and
    `hardware/new/' and so on. You get the idea.

    Therefore, within the folder `new/expensive/' you will find all files
    that have at least the tags "new" and "expensive" in any order. This is
    /really/ cool to have.

    Files of the current directory that don't have any tag at all, are
    linked directly to `~/.filetags' so that you can find and tag them
    easily.

    I personally, do use this feature within my image viewer of choice
    ([geeqie]). I mapped it to `Shift-T' because `Shift-t' is occupied by
    `filetags' for tagging of course. So when I am within my image viewer
    and I press `Shift-T', tagtrees of the currently shown images are
    created. Then an additional image viewer window opens up for me, showing
    the resulting tagtrees. This way, I can quickly navigate through the tag
    combinations to easily interactively filter according to tags.

    Please note: when you are tagging linked files within the tagtrees with
    filetags, only the current link gets updated with the new name. All
    other links to this modified filename within the other directories of
    the tagtrees gets broken. You have to re-create the tagtrees to update
    all the links after tagging files.


    [my PhD thesis] http://Karl-Voit.at/tagstore/downloads/Voit2012b.pdf

    [the tagstore webpage] http://Karl-Voit.at/tagstore/

    [linking] https://en.wikipedia.org/wiki/Symbolic_link

    [links] https://en.wikipedia.org/wiki/Symbolic_link

    [geeqie] http://geeqie.sourceforge.net/

    Valid combinations for ignore_nontagged and nontagged_subdir are:

    | ignore_nontagged | nontagged_subdir | results in ...                                                    |
    |------------------+------------------+-------------------------------------------------------------------|
    | False            | False            | non-linked items are linked to tagtrees root                      |
    | False            | <a string>       | non-linked items are linked to a tagtrees folder named <a string> |
    | True             | False            | non-linked items are ignored                                      |

    @param directory: the directory to use for generating the tagtrees hierarchy
    @param maxdepth: integer which holds the depth to which the tagtrees are generated; keep short to avoid HUGE execution times!
    @param ignore_nontagged: (bool) if True, non-tagged items are ignored and not linked
    @param nontagged_subdir: (string) holds a string containing the sub-directory name to link non-tagged items to
    @param link_missing_mutual_tagged_items: (bool) if True, any item that has a missing tag of any unique_tags entry is linked to a separate directory which is auto-generated from the unique_tags set names
    @param filtertags: (list) if options.tagfilter is used, this list holds the tags to filter for (AND)
    """

    assert_empty_tagfilter_directory(directory, options)

    # The boolean ignore_nontagged must be "False" when nontagged_subdir holds a value:
    # valid combinations:
    assert (ignore_nontagged and not nontagged_subdir) or (
        not ignore_nontagged and (not nontagged_subdir or nontagged_subdir is str)
    )

    # Extract the variables nontagged_item_dest_dir from the valid combinations
    # of nontagged_subdir and ignore_nontagged:
    nontagged_item_dest_dir = False  # ignore non-tagged items
    if nontagged_subdir:
        nontagged_item_dest_dir = os.path.join(directory, nontagged_subdir)
        assert_empty_tagfilter_directory(nontagged_item_dest_dir, options)
    elif not ignore_nontagged:
        nontagged_item_dest_dir = directory

    try:
        files = get_files_of_directory(os.getcwd(), options)
    except FileNotFoundError:
        error_exit(
            11,
            "When trying to look for files, I could not even find the current working directory. "
            + "Could it be the case that you've tried to generate tagtrees within the directory \""
            + directory
            + '"? '
            + "This would be a pity because filetags tends to delete and re-create this directory on each call of this feature. "
            + "Therefore, this directory does not exist after starting filetags and cleaning up the old content of it. "
            + "So it looks like we've got a shot-yourself-in-the-foot situation here … You can imagine that this was not "
            + "even simple to find and catch while testing for me either. Or was it? Make an educated guess. :-)",
        )

    if filtertags:
        logging.debug("generate_tagtrees: filtering tags ...")
        files = filter_files_matching_tags(files, filtertags)

    if len(files) == 0 and not options.recursive:
        error_exit(
            10,
            'There is no single file in the current directory "'
            + os.getcwd()
            + "\". I can't create "
            + "tagtrees from nothing. You gotta give me at least something to work with here, dude.",
        )

    # If a controlled vocabulary file is found for the directory where the tagtree
    # should be generated for, we link this file to the resulting tagtrees root
    # directory as well. This way, adding tags using tag completion also works for
    # the linked items.
    controlled_vocabulary_filename = locate_file_in_cwd_and_parent_directories(
        os.getcwd(), CONTROLLED_VOCABULARY_FILENAME
    )
    if controlled_vocabulary_filename:
        logging.debug(
            'generate_tagtrees: I found controlled_vocabulary_filename "'
            + controlled_vocabulary_filename
            + "\" which I'm going to link to the tagtrees folder"
        )
        if not options.dryrun:
            create_link(
                os.path.abspath(controlled_vocabulary_filename),
                os.path.join(directory, CONTROLLED_VOCABULARY_FILENAME),
                options=options
            )

    else:
        logging.debug(
            "generate_tagtrees: I did not find a controlled_vocabulary_filename"
        )

    logging.info(
        "Creating tagtrees and their links. It may take a while …  "
        + "(exponentially with respect to number of tags)"
    )

    tags = get_tags_from_files_and_subfolders(startdir=os.getcwd(), use_cache=True, options=options)

    # Here, we define a small helper function within a function. Cool,
    # heh? Bet many folks are not aware of those nifty things I know of ;-P
    def create_tagtrees_dir(basedirectory, tagpermutation):
        "Creates (empty) directories of the tagtrees directory structure"

        current_directory = os.path.join(
            basedirectory, *[x for x in tagpermutation]
        )  # flatten out list of permutations to elements
        # logging.debug('generate_tagtrees: mkdir ' + current_directory)
        if not options.dryrun and not os.path.exists(current_directory):
            os.makedirs(current_directory)

    # this generates a list whose elements (the tags) corresponds to
    # the filenames in the files list:
    tags_of_files = [extract_tags_from_filename(x) for x in files]

    # Firstly, let's iterate over the files, create tagtree
    # directories according to the set of tags from the current file
    # to avoid empty tagtree directories. Then we're going to link the
    # file to its tagtree directories. I'm confident that this is
    # going to be great.

    num_of_links = 0
    for currentfile in enumerate(files):

        tags_of_currentfile = tags_of_files[currentfile[0]]
        filename, dirname, basename, basename_without_lnk = split_up_filename(
            currentfile[1]
        )

        logging.debug('generate_tagtrees: handling file "' + filename + '" …')

        if len(tags_of_currentfile) == 0:
            # current file has no tags. It gets linked to the
            # nontagged_item_dest_dir folder (if set). This is somewhat handy to find files
            # which are - you guessed right - not tagged yet ;-)

            if ignore_nontagged:
                logging.debug(
                    'generate_tagtrees: file "'
                    + filename
                    + '" has no tags and will be ignores because of command line switch.'
                )
            else:
                logging.debug(
                    'generate_tagtrees: file "'
                    + filename
                    + '" has no tags. Linking to "'
                    + nontagged_item_dest_dir
                    + '"'
                )
                if not options.dryrun:
                    try:
                        create_link(
                            filename, os.path.join(nontagged_item_dest_dir, basename, options=options)
                        )
                    except FileExistsError:
                        logging.warning(
                            'Untagged file "'
                            + filename
                            + '" is already linked: "'
                            + os.path.join(nontagged_item_dest_dir, basename)
                            + '". You must have used the recursive '
                            + "option and the sub-tree you're generating a "
                            + "tagtree from has two times the "
                            + "same filename. I stick with the first one."
                        )
                num_of_links += 1

        else:

            # Here we go: current file has at least one tag. Create
            # its tagtree directories and link the file:

            # logging.debug('generate_tagtrees: permutations for file: "' + filename + '"')
            for currentdepth in range(1, maxdepth + 1):
                # logging.debug('generate_tagtrees: currentdepth: ' + str(currentdepth))
                for tagpermutation in itertools.permutations(
                    tags_of_currentfile, currentdepth
                ):

                    # WHAT I THOUGHT:
                    # Creating the directories does not require to iterate
                    # over the different level of depth because
                    # "os.makedirs()" is able to create all parent folders
                    # that are necessary. This spares us a loop.
                    # WHAT I LEARNED:
                    # We *have* to iterate over the depth as well
                    # because when a file has only one tag and the
                    # maxdepth is more than one, we are forgetting
                    # to create all those tagtree directories for this
                    # single tag. Therefore: we need to depth-loop for
                    # creating the directories as well. Bummer.
                    create_tagtrees_dir(directory, tagpermutation)

                    current_directory = os.path.join(
                        directory, *[x for x in tagpermutation]
                    )  # flatten out list of permutations to elements
                    # logging.debug('generate_tagtrees: linking file in ' + current_directory)
                    if not options.dryrun:
                        try:
                            create_link(
                                filename, os.path.join(current_directory, basename), options=options
                            )
                        except FileExistsError:
                            logging.warning(
                                'Tagged file "'
                                + filename
                                + '" is already linked: "'
                                + os.path.join(current_directory, basename)
                                + '". You must have used the recursive '
                                + "option and the sub-tree you're generating "
                                + "a tagtree from has two times the same "
                                + "filename. I stick with the first one."
                            )
                    num_of_links += 1

            if link_missing_mutual_tagged_items:
                # REFACTOR: Move to function params.
                for unique_tagset in unique_tags:

                    # Oh yes, I do wish I had solved the default teststring issue in
                    # a cleaner way. Ignore it here hard-coded.
                    if unique_tagset == ["teststring1", "teststring2"]:
                        continue

                    # When there is no intersection between the item tags and the current unique_tagset ...
                    if not set(tags_of_currentfile).intersection(set(unique_tagset)):

                        # ... generate a no-$unique_tagset directory ...
                        no_uniqueset_tag_found_dir = os.path.join(
                            directory, "no-" + ("-").join(unique_tagset)
                        )  # example: "no-draft-final"
                        if not os.path.isdir(no_uniqueset_tag_found_dir):
                            logging.debug(
                                'generate_tagtrees: creating non-existent no_uniqueset_tag_found_dir "%s" ...'
                                % str(no_uniqueset_tag_found_dir)
                            )
                            if not options.dryrun:
                                os.makedirs(no_uniqueset_tag_found_dir)

                        # ... and link the item into it:
                        if not options.dryrun:
                            try:
                                create_link(
                                    filename,
                                    os.path.join(no_uniqueset_tag_found_dir, basename),
                                    options=options
                                )
                            except FileExistsError:
                                logging.warning(
                                    'Tagged file "'
                                    + filename
                                    + '" is already linked: "'
                                    + os.path.join(no_uniqueset_tag_found_dir, basename)
                                    + '". I stick with the first one.'
                                )
                        num_of_links += 1

    # Brag about how brave I was. And: it also shows the user why the
    # runtime was that long. The number of links grows exponentially
    # with the number of tags. Keep this in mind when tempering with
    # the maxdepth!
    logging.info(
        'Number of links created in "'
        + directory
        + '" for the '
        + str(len(files))
        + " files: "
        + str(num_of_links)
        + "  (tagtrees depth is "
        + str(maxdepth)
        + ")"
    )


def handle_option_tagtrees(filtertags=None):
    """
    Handles the options and preprocessing for generating tagtrees.

    @param: filtertags: (list) if options.tagfilter is used, this list contains the user-entered list of tags to filter for
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

    # FIXXME 2018-04-04: following 4-lines block re-occurs for options.tagfilter: unify accordingly!
    chosen_tagtrees_dir = TAGFILTER_DIRECTORY
    if options.tagtrees_directory:
        chosen_tagtrees_dir = options.tagtrees_directory[0]
        logging.debug(
            "User overrides the default tagtrees directory to: "
            + str(chosen_tagtrees_dir)
        )

    start = time.time()
    generate_tagtrees(
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
