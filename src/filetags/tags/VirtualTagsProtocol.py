from typing import Protocol

from filetags.common.types import Filenames, Tagnames, TagnamesVocabulary
from filetags.tags.services import TagService


# TODO: Make VirtualTags follow this protocol (ABC?). Currently we maintain it manually.
class VirtualTagsProtocol(Protocol):
    @property
    def current_service(self) -> TagService: ...

    unique_tags: Tagnames

    def filter_files_matching_tags(
        self, files: Filenames, tags: TagnamesVocabulary
    ) -> Filenames: ...
