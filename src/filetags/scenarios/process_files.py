import logging
import os

from filetags.cli.parser.options import CliOptions
from filetags.file_operations.links import is_broken_link
from filetags.scenarios.common import Files
from filetags.scenarios.file_handlers import handle_file_and_optional_link
from filetags.utils.logging import error_exit


def process_files(
    files: Files, filtertags, list_of_link_directories, max_file_length: int, options: CliOptions = {}
):
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
                max_file_length=max_file_length,
                options=options,
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
