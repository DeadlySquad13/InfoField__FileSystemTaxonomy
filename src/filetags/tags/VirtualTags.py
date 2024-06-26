from dataclasses import dataclass, field
from typing import Literal

from filetags.common.types import Filenames, Tagnames, TagnamesVocabulary
from filetags.tag_gardening import TagGardening
from filetags.tags.repr import TagRepr
from filetags.tags.services import TagLocalFilesystem, TagService
from filetags.Tagtree import Tagtree
from filetags.Vocabulary import Vocabulary

# TOOO: Automate it. Names in services?
TagServiceName = Literal["local_filesystem"]


@dataclass
class VirtualTags(TagRepr, Tagtree, Vocabulary, TagGardening):
    _current_service_name: TagServiceName
    unique_tags: Tagnames = field(default_factory=list)
    services: dict[TagServiceName, TagService] = field(default_factory=dict)
    # QUESTION: We need to work with one service simultaneously? Or with all at
    # once?

    def __init__(self):
        self.unique_tags = []
        self.services = {}
        self.services["local_filesystem"] = TagLocalFilesystem()

        self._current_service_name = "local_filesystem"

    @property
    def current_service(self):
        return self.services[self._current_service_name]

    def get_unique_tags_from_filename(self, filename):
        """
        Extracts tags that occur in the array of arrays "unique_tags".

        @param filename: string containing one file name
        @param return: list of found tags
        """

        filetags = self.current_service.extract_tags_from_filename(filename)
        result = []
        for tag in filetags:
            for taggroup in self.unique_tags:
                if tag in taggroup:
                    result.append(tag)
        return result

    def list_unknown_tags(self, file_tag_dict):
        """
        Traverses the file system, extracts all tags, prints tags that are found
        in file names which are not found in the controlled vocabulary file .filetags

        @param return: dict of tags (if max_tag_count is set, returned entries are set accordingly)
        """

        # REFACTOR: False as a param?
        vocabulary = self.locate_and_parse_controlled_vocabulary(False)

        # filter out known tags from tag_dict
        unknown_tag_dict = {
            key: value
            for key, value in list(file_tag_dict.items())
            if key not in vocabulary
        }

        if unknown_tag_dict:
            self.print_tag_dict(unknown_tag_dict, vocabulary)
        else:
            print(
                "\n  "
                + str(len(file_tag_dict))
                + " different tags were found in file names which are all"
                + " part of your .filetags vocabulary (consisting of "
                + str(len(vocabulary))
                + " tags).\n"
            )

        return unknown_tag_dict

    def filter_files_matching_tags(
        self, files: Filenames, tags: TagnamesVocabulary
    ) -> Filenames:
        """
        Returns a list of file names that contain all given tags.

        @param allfiles: array of file names
        @param tags: array of tags
        @param return: list of file names that contain all tags
        """

        return [
            x
            for x in files
            if set(self.current_service.extract_tags_from_filename(x)).issuperset(
                set(tags)
            )
        ]
