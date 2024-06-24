import os
import re
import platform


IS_WINDOWS = platform.system() == "Windows"
PROG_VERSION = "Time-stamp: <2024-01-13 18:29:18 vk>"
PROG_VERSION_DATE = PROG_VERSION[13:23]
# Unused: INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
# TODO: Move to user settings?
FILENAME_TAG_SEPARATOR = " -- "
BETWEEN_TAG_SEPARATOR = " "
CONTROLLED_VOCABULARY_FILENAME = ".filetags"
HINT_FOR_BEING_IN_VOCABULARY_TEMPLATE = " *"
TAGFILTER_DIRECTORY = os.path.join(os.path.expanduser("~"), ".filetags_tagfilter")
# Be careful when making this more than 2: exponential growth of time/links with number of tags!
DEFAULT_TAGTREES_MAXDEPTH = 2
DEFAULT_IMAGE_VIEWER_LINUX = "geeqie"
DEFAULT_IMAGE_VIEWER_WINDOWS = "explorer"
TAG_LINK_ORIGINALS_WHEN_TAGGING_LINKS = True


# file names containing tags matches following regular expression
FILE_WITH_TAGS_REGEX = re.compile(
    r"(.+?)" + FILENAME_TAG_SEPARATOR + r"(.+?)(\.(\w+))??$"
)
FILE_WITH_TAGS_REGEX_FILENAME_INDEX = 1  # component.group(1)
FILE_WITH_TAGS_REGEX_TAGLIST_INDEX = 2
FILE_WITH_TAGS_REGEX_EXTENSION_INDEX = 4

FILE_WITH_EXTENSION_REGEX = re.compile(r"(.*)\.(.*)$")
FILE_WITH_EXTENSION_REGEX_FILENAME_INDEX = 1
FILE_WITH_EXTENSION_REGEX_EXTENSION_INDEX = 2


YYYY_MM_DD_PATTERN = re.compile(r"^(\d{4,4})-([01]\d)-([0123]\d)[- _T]")
