# import win32com
import logging
import os

from filetags.cli.parser import CliOptions
from filetags.consts import TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS
from filetags.file_operations.find_unique_alternative_to_file import \
    find_unique_alternative_to_file
from filetags.file_operations.links import (create_link, get_link_source_file,
                                            is_lnk_file, is_nonbroken_link,
                                            split_up_filename)
from filetags.tags.VirtualTags import VirtualTags
from filetags.utils.data_structures import (item_contained_in_list_of_lists,
                                            print_item_transition)


# REFACTOR: abstract tags and file_operations functionality.
def handle_file_and_optional_link(
    virtualTags: VirtualTags,
    orig_filename,
    tags,
    do_remove,
    do_filter,
    dryrun,
    max_file_length,
    options: CliOptions = {},
):
    """
    @param orig_filename: string containing one file name
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: number of errors and optional new filename
    """

    num_errors = 0
    original_dir = os.getcwd()
    logging.debug(
        'handle_file_and_optional_link("' + orig_filename + '") …  ' + "★" * 20
    )
    logging.debug("handle_file_and_optional_link: original directory = " + original_dir)

    if os.path.isdir(orig_filename):
        logging.warning(
            'Skipping directory "%s" because this tool only renames file names.'
            % orig_filename
        )
        return num_errors, False

    filename, dirname, basename, basename_without_lnk = split_up_filename(orig_filename)
    global list_of_link_directories

    if not (os.path.isfile(filename) or os.path.islink(filename)):
        logging.debug(
            "handle_file_and_optional_link: this is no regular file nor a link; "
            + "looking for an alternative file that starts with same substring …"
        )

        # try to find unique alternative file:
        alternative_filename = find_unique_alternative_to_file(filename)

        if not alternative_filename:
            logging.debug(
                "handle_file_and_optional_link: Could not locate alternative "
                + "basename that starts with same substring"
            )
            logging.error(
                'Skipping "%s" because this tool only renames existing file names.'
                % filename
            )
            num_errors += 1
            return num_errors, False
        else:
            logging.info(
                'Could not find basename "%s" but found "%s" instead which starts with same substring ...'
                % (filename, alternative_filename)
            )
            filename, dirname, basename, basename_without_lnk = split_up_filename(
                alternative_filename
            )

    if dirname and os.getcwd() != dirname:
        logging.debug('handle_file_and_optional_link: changing to dir "%s"' % dirname)
        os.chdir(dirname)
    # else:
    #     logging.debug("handle_file_and_optional_link: no dirname found or os.getcwd() is dirname")

    # if basename is a link and has same basename, tag the source file as well:
    if TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS and is_nonbroken_link(filename):
        logging.debug(
            "handle_file_and_optional_link: file is a non-broken link (and "
            + "TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS is set)"
        )

        (
            old_source_filename,
            old_source_dirname,
            old_source_basename,
            old_source_basename_without_lnk,
        ) = split_up_filename(get_link_source_file(filename))

        linkbasename_same_as_originalbasename = False
        if is_lnk_file(basename):
            linkbasename_same_as_originalbasename = (
                old_source_basename == basename[:-4]
            )  # remove ending '.lnk'
        else:
            linkbasename_same_as_originalbasename = old_source_basename == basename

        if linkbasename_same_as_originalbasename:
            logging.debug(
                'handle_file_and_optional_link: link "'
                + filename
                + '" has same basename as its source file "'
                + old_source_filename
                + '"  '
                + "v" * 20
            )

            logging.debug(
                'handle_file_and_optional_link: invoking handle_file_and_optional_link("'
                + old_source_filename
                + '")  '
                + "v" * 20
            )
            additional_errors, new_source_basename = handle_file_and_optional_link(
                old_source_filename, tags, do_remove, do_filter, dryrun
            )
            num_errors += additional_errors
            logging.debug(
                'handle_file_and_optional_link: RETURNED handle_file_and_optional_link("'
                + old_source_filename
                + '")  '
                + "v" * 20
            )

            # FIX: 2018-06-02: introduced to debug https://github.com/novoid/filetags/issues/22
            logging.debug("old_source_dirname: [" + old_source_dirname + "]")
            logging.debug("new_source_basename: [" + new_source_basename + "]")

            new_source_filename = os.path.join(old_source_dirname, new_source_basename)
            (
                new_source_filename,
                new_source_dirname,
                new_source_basename,
                new_source_basename_without_lnk,
            ) = split_up_filename(new_source_filename)

            if old_source_basename != new_source_basename:
                logging.debug(
                    'handle_file_and_optional_link: Tagging the symlink-destination file of "'
                    + basename
                    + '" ("'
                    + old_source_filename
                    + '") as well …'
                )

                if options.dryrun:
                    logging.debug(
                        'handle_file_and_optional_link: I would re-link the old sourcefilename "'
                        + old_source_filename
                        + '" to the new one "'
                        + new_source_filename
                        + '"'
                    )
                else:
                    new_filename = os.path.join(
                        dirname, new_source_basename_without_lnk
                    )
                    logging.debug(
                        'handle_file_and_optional_link: re-linking link "'
                        + new_filename
                        + '" from the old sourcefilename "'
                        + old_source_filename
                        + '" to the new one "'
                        + new_source_filename
                        + '"'
                    )
                    os.remove(filename)
                    create_link(new_source_filename, new_filename, options=options)
                # we've already handled the link source and created the updated link, return now without calling handle_file once more ...
                os.chdir(
                    dirname
                )  # go back to original dir after handling links of different directories
                return num_errors, new_filename
            else:
                logging.debug(
                    'handle_file_and_optional_link: The old sourcefilename "'
                    + old_source_filename
                    + "\" did not change. So therefore I don't re-link."
                )
                # we've already handled the link source and created the updated link, return now without calling handle_file once more ...
                os.chdir(
                    dirname
                )  # go back to original dir after handling links of different directories
                return num_errors, old_source_filename
        else:
            logging.debug(
                'handle_file_and_optional_link: The file "'
                + filename
                + '" is a link to "'
                + old_source_filename
                + '" but they two do have different basenames. Therefore I ignore the original file.'
            )
        os.chdir(
            dirname
        )  # go back to original dir after handling links of different directories
    else:
        logging.debug(
            "handle_file_and_optional_link: file is not a non-broken link ("
            + repr(is_nonbroken_link(basename))
            + ") or TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS is not set"
        )

    logging.debug(
        "handle_file_and_optional_link: after handling potential link originals, I now handle "
        + "the file we were talking about in the first place: "
        + filename
    )

    new_filename = handle_file(
        virtualTags,
        filename,
        tags,
        do_remove,
        do_filter,
        dryrun,
        max_file_length=max_file_length,
        options=options,
    )

    logging.debug(
        "handle_file_and_optional_link: switching back to original directory = "
        + original_dir
    )
    os.chdir(original_dir)  # reset working directory
    logging.debug(
        'handle_file_and_optional_link("' + orig_filename + '") FINISHED  ' + "★" * 20
    )
    return num_errors, new_filename


# REFACTOR: abstract tags functionality.
def handle_file(
    virtualTags,
    orig_filename,
    tags,
    do_remove,
    do_filter,
    dryrun,
    max_file_length,
    options: CliOptions = {},
):
    """
    @param orig_filename: string containing one file name with absolute path
    @param tags: list containing one or more tags
    @param do_remove: boolean which defines if tags should be added (False) or removed (True)
    @param dryrun: boolean which defines if files should be changed (False) or not (True)
    @param return: error value or new filename
    """

    assert orig_filename.__class__ == str
    assert tags.__class__ == list
    if do_remove:
        assert do_remove.__class__ == bool
    if do_filter:
        assert do_filter.__class__ == bool
    if dryrun:
        assert dryrun.__class__ == bool

    global chosen_tagtrees_dir

    filename, dirname, basename, basename_without_lnk = split_up_filename(
        orig_filename, exception_on_file_not_found=True
    )

    logging.debug(
        'handle_file("'
        + filename
        + '") '
        + "#" * 10
        + '  … with working dir "'
        + os.getcwd()
        + '"'
    )

    if do_filter:
        print_item_transition(
            dirname,
            basename,
            chosen_tagtrees_dir,
            transition="link",
            max_file_length=max_file_length,
        )
        if not dryrun:
            create_link(
                filename, os.path.join(chosen_tagtrees_dir, basename), options=options
            )

    else:  # add or remove tags:
        new_basename = basename
        logging.debug(
            "handle_file: set new_basename ["
            + new_basename
            + "] according to parameters (initialization)"
        )

        for tagname in tags:
            if tagname.strip() == "":
                continue
            if do_remove:
                new_basename = virtualTags.current_service.removing_tag_from_filename(
                    new_basename, tagname
                )
                logging.debug(
                    "handle_file: set new_basename ["
                    + new_basename
                    + "] when do_remove"
                )
            elif tagname[0] == "-":
                new_basename = virtualTags.current_service.removing_tag_from_filename(
                    new_basename, tagname[1:]
                )
                logging.debug(
                    "handle_file: set new_basename ["
                    + new_basename
                    + "] when tag starts with a minus"
                )
            else:
                # FIXXME: not performance optimized for large number of unique tags in many lists:
                tag_in_unique_tags, matching_unique_tag_list = (
                    item_contained_in_list_of_lists(tagname, virtualTags.unique_tags)
                )

                if tagname != tag_in_unique_tags:
                    new_basename = virtualTags.current_service.adding_tag_to_filename(
                        new_basename, tagname
                    )
                    logging.debug(
                        "handle_file: set new_basename ["
                        + new_basename
                        + "] when tagname != tag_in_unique_tags"
                    )
                else:
                    # if tag within unique_tags found, and new unique tag is given, remove old tag:
                    # e.g.: unique_tags = (u'yes', u'no') -> if 'no' should be added, remove existing tag 'yes' (and vice versa)
                    # If user enters contradicting tags, only the last one will be applied.
                    # FIXXME: this is an undocumented feature -> please add proper documentation

                    current_filename_tags = (
                        virtualTags.current_service.extract_tags_from_filename(
                            new_basename
                        )
                    )
                    conflicting_tags = list(
                        set(current_filename_tags).intersection(
                            matching_unique_tag_list
                        )
                    )
                    logging.debug(
                        "handle_file: found unique tag %s which require old unique tag(s) to be removed: %s"
                        % (tagname, repr(conflicting_tags))
                    )
                    for conflicting_tag in conflicting_tags:
                        new_basename = (
                            virtualTags.current_service.removing_tag_from_filename(
                                new_basename, conflicting_tag
                            )
                        )
                        logging.debug(
                            "handle_file: set new_basename ["
                            + new_basename
                            + "] when conflicting_tag in conflicting_tags"
                        )
                    new_basename = virtualTags.current_service.adding_tag_to_filename(
                        new_basename, tagname
                    )
                    logging.debug(
                        "handle_file: set new_basename ["
                        + new_basename
                        + "] after adding_tag_to_filename()"
                    )

        new_filename = os.path.join(dirname, new_basename)

        if do_remove:
            transition = "delete"
        else:
            transition = "add"

        if basename != new_basename:

            list_of_link_directories.append(dirname)

            if len(list_of_link_directories) > 1:
                logging.debug(
                    "new_filename is a symlink. Screen output of transistion gets postponed to later on."
                )
            # REFACTOR: Change options to a function parameter.
            elif not options.quiet:
                print_item_transition(
                    dirname,
                    basename,
                    new_basename,
                    transition=transition,
                    max_file_length=max_file_length,
                )

            if not dryrun:
                os.rename(filename, new_filename)

        logging.debug('handle_file("' + filename + '") ' + "#" * 10 + "  finished")
        return new_filename
