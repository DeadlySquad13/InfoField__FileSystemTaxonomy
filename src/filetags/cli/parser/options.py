import argparse
import sys

from filetags.cli.help_parts import DESCRIPTION, EPILOG
from filetags.consts import (DEFAULT_IMAGE_VIEWER_LINUX,
                             DEFAULT_TAGTREES_MAXDEPTH, TAGFILTER_DIRECTORY)

CliOptions = argparse.Namespace


def get_cli_options():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        # keep line breaks in EPILOG and such
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
        description=DESCRIPTION,
    )

    parser.add_argument(
        dest="files", metavar="FILE", nargs="*", help="One or more files to tag"
    )

    parser.add_argument(
        "-t",
        "--tags",
        dest="tags",
        nargs=1,
        type=str,
        metavar='"STRING WITH TAGS"',
        required=False,
        help="One or more tags (in quotes, separated by spaces) to add/remove",
    )

    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove tags from (instead of adding to) file name(s)",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        dest="interactive",
        help="Interactive mode: ask for (a)dding or (r)emoving and name of tag(s)",
    )

    parser.add_argument(
        "-R",
        "--recursive",
        dest="recursive",
        action="store_true",
        help="Recursively go through the current directory and all of its subdirectories. "
        + "Implemented for --tag-gardening and --tagtrees",
    )

    parser.add_argument(
        "-s",
        "--dryrun",
        dest="dryrun",
        action="store_true",
        help="Enable dryrun mode: just simulate what would happen, do not modify files",
    )

    parser.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_true",
        help="If a link is about to be created and a previous file/link exists, the old will be deleted if this is enabled.",
    )

    parser.add_argument(
        "--hardlinks",
        dest="hardlinks",
        action="store_true",
        help="Use hard links instead of symbolic links. This is ignored on Windows systems. "
        + "Note that renaming link originals when tagging does not work with hardlinks.",
    )

    parser.add_argument(
        "-f",
        "--filter",
        dest="tagfilter",
        action="store_true",
        help='Ask for list of tags and generate links in "'
        + TAGFILTER_DIRECTORY
        + '" '
        + "containing links to all files with matching tags and start the filebrowser. "
        + "Target directory can be overridden by --tagtrees-dir.",
    )

    parser.add_argument(
        "--filebrowser",
        dest="filebrowser",
        metavar="PATH_TO_FILEBROWSER",
        help="Use this option to override the tool to view/manage files (for --filter; default: "
        + DEFAULT_IMAGE_VIEWER_LINUX
        + '). Use "none" to omit the default one.',
    )

    parser.add_argument(
        "--tagtrees",
        dest="tagtrees",
        action="store_true",
        help='This generates nested directories in "'
        + TAGFILTER_DIRECTORY
        + '" for each combination of tags '
        + "up to a limit of "
        + str(DEFAULT_TAGTREES_MAXDEPTH)
        + ". Target directory "
        + "can be overridden by --tagtrees-dir. "
        + "Please note that this may take long since it relates "
        + "exponentially to the number of tags involved. Can be combined with --filter. "
        + "See also http://Karl-Voit.at/tagstore/ and http://Karl-Voit.at/tagstore/downloads/Voit2012b.pdf",
    )

    parser.add_argument(
        "--tagtrees-handle-no-tag",
        dest="tagtrees_handle_no_tag",
        nargs=1,
        type=str,
        metavar='"treeroot" | "ignore" | "FOLDERNAME"',
        required=False,
        help="When tagtrees are created, this parameter defines how to handle items that got "
        + "no tag at all. "
        + 'The value "treeroot" is the default behavior: items without a tag are linked to '
        + "the tagtrees root. "
        + 'The value "ignore" will not link any non-tagged items at all. '
        + "Any other value is interpreted as a folder name within the tagreees which is used "
        + "to link all non-tagged items to.",
    )

    parser.add_argument(
        "--tagtrees-link-missing-mutual-tagged-items",
        dest="tagtrees_link_missing_mutual_tagged_items",
        action="store_true",
        help="When the controlled vocabulary holds mutual exclusive tags (multiple tags in one line) "
        + "this option generates directories in the tagtrees root that hold links to items that have no "
        + 'single tag from those mutual exclusive sets. For example, when "draft final" is defined in the vocabulary, '
        + 'all items without "draft" and "final" are linked to the "no-draft-final" directory.',
    )

    parser.add_argument(
        "--tagtrees-dir",
        dest="tagtrees_directory",
        nargs=1,
        type=str,
        metavar="<existing_directory>",
        required=False,
        help="When tagtrees are created, this parameter overrides the default "
        + 'target directory "'
        + TAGFILTER_DIRECTORY
        + '" with a user-defined one. It has to be an empty directory or a '
        + "non-existing directory which will be created. "
        + "This also overrides the default directory for --filter.",
    )

    parser.add_argument(
        "--tagtrees-depth",
        dest="tagtrees_depth",
        nargs=1,
        type=int,
        required=False,
        help="When tagtrees are created, this parameter defines the level of "
        + "depth of the tagtree hierarchy. "
        + "The default value is 2. Please note that increasing the depth "
        + "increases the number of links exponentially. "
        + "Especially when running Windows (using lnk-files instead of "
        + "symbolic links) the performance is really slow. "
        + "Choose wisely.",
    )

    parser.add_argument(
        "--ln",
        "--list-tags-by-number",
        dest="list_tags_by_number",
        action="store_true",
        help="List all file-tags sorted by their number of use",
    )

    parser.add_argument(
        "--la",
        "--list-tags-by-alphabet",
        dest="list_tags_by_alphabet",
        action="store_true",
        help="List all file-tags sorted by their name",
    )

    parser.add_argument(
        "--lu",
        "--list-tags-unknown-to-vocabulary",
        dest="list_unknown_tags",
        action="store_true",
        help="List all file-tags which are found in file names but are not part of .filetags",
    )

    parser.add_argument(
        "--tag-gardening",
        dest="tag_gardening",
        action="store_true",
        help="This is for getting an overview on tags that might require to be renamed (typos, "
        + "singular/plural, ...). See also http://www.webology.org/2008/v5n3/a58.html",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose mode",
    )

    parser.add_argument(
        "-q", "--quiet", dest="quiet", action="store_true", help="Enable quiet mode"
    )

    parser.add_argument(
        "--version",
        dest="version",
        action="store_true",
        help="Display version and exit",
    )

    return parser.parse_args()
