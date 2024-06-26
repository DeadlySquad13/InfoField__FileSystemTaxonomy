import os
from abc import ABCMeta
from dataclasses import dataclass

from filetags.cli.parser import CliOptions
from filetags.common.types import Filename, Tagname, Tagnames


@dataclass()
class TagService(metaclass=ABCMeta):
    def contains_tag(self, filename: str, tagname=False) -> bool: ...
    def extract_tags_from_filename(self, filename: str) -> Tagnames: ...
    def extract_tags_from_path(self, path: str) -> Tagnames: ...

    def adding_tag_to_filename(
        self, filename: Filename, tagname: Tagname
    ) -> Filename: ...

    def removing_tag_from_filename(
        self, orig_filename: Filename, tagname: Tagname
    ) -> Filename: ...

    def get_tags_from_files_and_subfolders(
        self,
        startdir=os.getcwd(),
        use_cache=True,
        cache_of_files_with_metadata={},
        options: CliOptions = {},
    ): ...
