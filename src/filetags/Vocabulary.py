import codecs  # for handling Unicode content in .tagfiles
import logging
import os

from filetags.consts import (BETWEEN_TAG_SEPARATOR,
                             CONTROLLED_VOCABULARY_FILENAME, IS_WINDOWS)
from filetags.file_operations import (
    get_link_source_file, is_lnk_file, is_nonbroken_link,
    locate_file_in_cwd_and_parent_directories)
from filetags.common.types import Tagnames
from filetags.tags.VirtualTagsProtocol import VirtualTagsProtocol

# those tags are omitted from being suggested when they are mentioned in .filetags #donotsuggest lines (case insensitive)
# example line:  "#donotsuggest foo bar" -> "foo" and "bar" are never suggested
DONOTSUGGEST_PREFIX = "#donotsuggest "


class Vocabulary:
    """
    Controlled vocabulary - list of predefined tags.

    Expected to be used as mixin in class following VirtualTagsProtocol.
    """

    do_not_suggest_tags: Tagnames = []

    def locate_and_parse_controlled_vocabulary(self: VirtualTagsProtocol, startfile):
        """This method is looking for files named
        CONTROLLED_VOCABULARY_FILENAME in the directory of startfile and parses
        it. Each line contains a tag which gets read in for tab
        completion.

        @param startfile: file whose location is the starting point of the search
        @param return: either False or a list of found tag strings

        """

        logging.debug(
            'locate_and_parse_controlled_vocabulary: called with startfile: "'
            + str(startfile)
            + '"'
        )
        logging.debug(
            "locate_and_parse_controlled_vocabulary: called in cwd: " + str(os.getcwd())
        )
        if startfile:
            filename = locate_file_in_cwd_and_parent_directories(
                startfile, CONTROLLED_VOCABULARY_FILENAME
            )
        else:
            filename = locate_file_in_cwd_and_parent_directories(
                os.getcwd(), CONTROLLED_VOCABULARY_FILENAME
            )

        if filename:
            logging.debug(
                "locate_and_parse_controlled_vocabulary: locate_file_in_cwd_and_parent_directories returned: "
                + filename
            )
        else:
            logging.debug(
                "locate_and_parse_controlled_vocabulary: locate_file_in_cwd_and_parent_directories did NOT find any filename"
            )

        if IS_WINDOWS:
            # searching for and handling of lnk files:
            logging.debug(
                "locate_and_parse_controlled_vocabulary: this is Windows: "
                + "also look out for lnk-files that link to .filetags files ..."
            )
            if startfile:
                lnk_filename = locate_file_in_cwd_and_parent_directories(
                    startfile, CONTROLLED_VOCABULARY_FILENAME + ".lnk"
                )
            else:
                lnk_filename = locate_file_in_cwd_and_parent_directories(
                    os.getcwd(), CONTROLLED_VOCABULARY_FILENAME + ".lnk"
                )

            if lnk_filename and filename:
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: this is Windows: "
                    + "both (non-lnk and lnk) .filetags found. Taking the one with the longer path"
                )
                if os.path.dirname(lnk_filename) > os.path.dirname(
                    filename
                ) and is_nonbroken_link(lnk_filename):
                    logging.debug(
                        "locate_and_parse_controlled_vocabulary: this is Windows: "
                        + "taking the lnk .filetags"
                    )
                    filename = lnk_filename
                elif not is_nonbroken_link(lnk_filename):
                    logging.debug(
                        "locate_and_parse_controlled_vocabulary: this is Windows: "
                        + "taking the non-lnk .filetags since the found lnk is a broken link"
                    )
            elif lnk_filename and not filename:
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: this is Windows: "
                    + "only a lnk of .filetags was found"
                )
                filename = lnk_filename
            else:
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: this is Windows: "
                    + ".filetags (non-lnk) was found"
                )

            if (
                filename
                and is_lnk_file(filename)
                and os.path.isfile(get_link_source_file(filename))
            ):
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: this is Windows: "
                    + "set filename to source file for lnk .filetags"
                )
                filename = get_link_source_file(filename)

        if filename:
            logging.debug(
                "locate_and_parse_controlled_vocabulary: .filetags found: " + filename
            )
            if os.path.isfile(filename):
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: found controlled vocabulary"
                )

                tags = []
                with codecs.open(filename, encoding="utf-8") as filehandle:
                    logging.debug(
                        "locate_and_parse_controlled_vocabulary: reading controlled vocabulary in [%s]"
                        % filename
                    )
                    global controlled_vocabulary_filename
                    controlled_vocabulary_filename = filename
                    for rawline in filehandle:

                        if rawline.strip().lower().startswith(DONOTSUGGEST_PREFIX):
                            # parse and save do not suggest tags:
                            line = rawline[len(DONOTSUGGEST_PREFIX) :].strip().lower()
                            for tag in line.split(BETWEEN_TAG_SEPARATOR):
                                self.do_not_suggest_tags.append(tag)
                        else:

                            # remove everyting after the first hash character (which is a comment separator)
                            line = (
                                rawline.strip().split("#")[0].strip()
                            )  # split and take everything before the first '#' as new "line"

                            if len(line) == 0:
                                # nothing left, line consisted only of a comment or was empty
                                continue

                            if BETWEEN_TAG_SEPARATOR in line:
                                ## if multiple tags are in one line, they are mutually exclusive: only has can be set via filetags
                                logging.debug(
                                    "locate_and_parse_controlled_vocabulary: found unique tags: %s"
                                    % (line)
                                )
                                self.unique_tags.append(
                                    line.split(BETWEEN_TAG_SEPARATOR)
                                )
                                for tag in line.split(BETWEEN_TAG_SEPARATOR):
                                    # *also* append unique tags to general tag list:
                                    tags.append(tag)
                            else:
                                tags.append(line)

                logging.debug(
                    "locate_and_parse_controlled_vocabulary: controlled vocabulary has %i tags"
                    % len(tags)
                )
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: controlled vocabulary has %i groups of unique tags"
                    % (len(self.unique_tags) - 1)
                )

                return tags
            else:
                logging.debug(
                    "locate_and_parse_controlled_vocabulary: controlled vocabulary is a non-existing file"
                )
                return []
        else:
            logging.debug(
                "locate_and_parse_controlled_vocabulary: could not derive filename for controlled vocabulary"
            )
            return []
