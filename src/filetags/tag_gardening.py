import os

from filetags.cli.parser import CliOptions
from filetags.common.consts import UNIQUE_TAG_TESTSTRINGS
from filetags.file_operations import get_files_with_metadata
from filetags.tags.VirtualTagsProtocol import VirtualTagsProtocol


# REFACTOR: Some methods on self are not typed. Partly because protocol is raw
# but what is more important that some are present in TagRepr.
class TagGardening:
    """
    TagGardening - realization for maintaining created tags, ensuring
    that the information is relevant.

    Expected to be used as mixin in class following VirtualTagsProtocol.
    """

    def handle_tag_gardening(
        self: VirtualTagsProtocol,
        vocabulary,
        cache_of_files_with_metadata={},
        options: CliOptions = {},
    ):
        """
        This method is quite handy to find tags that might contain typos or do not
        differ much from other tags. You might want to rename them accordinly.

        Tags are gathered from the file system.

        Tags that appear also in the vocabulary get marked in the output.

        @param vocabulary: array containing the controlled vocabulary (or False)
        @param return: -
        """

        files_with_metadata = get_files_with_metadata(
            startdir=os.getcwd(),
            cache_of_files_with_metadata=cache_of_files_with_metadata,
            options=options,
        )  # = cache_of_files_with_metadata of current dir
        tag_dict = self.current_service.get_tags_from_files_and_subfolders(
            startdir=os.getcwd(), options=options
        )
        if not tag_dict:
            print("\nNo file containing tags found in this folder hierarchy.\n")
            return

        print("\nYou have used " + str(len(tag_dict)) + " tags in total.\n")

        number_of_files = len(files_with_metadata)
        print(
            "\nNumber of total files:                           " + str(number_of_files)
        )

        def str_percentage(fraction, total):
            "returns a string containing the percentage of the fraction wrt the total"
            assert fraction is int
            assert total is int
            if total == 0:
                return "0%"  # avoid division by zero
            else:
                return str(round(100 * fraction / total, 1)) + "%"

        files_without_alltags = [x for x in files_with_metadata if not x["alltags"]]
        num_files_without_alltags = len(files_without_alltags)

        files_without_filetags = [x for x in files_with_metadata if not x["filetags"]]
        num_files_without_filetags = len(files_without_filetags)

        num_files_with_alltags = number_of_files - len(files_without_alltags)

        files_with_filetags = [x for x in files_with_metadata if x["filetags"]]
        num_files_with_filetags = len(files_with_filetags)

        print(
            "\nNumber of files without tags including pathtags: "
            + str(num_files_without_alltags)
            + "   ("
            + str_percentage(num_files_without_alltags, number_of_files)
            + " of total files)"
        )

        print(
            "Number of files without filetags:                "
            + str(num_files_without_filetags)
            + "   ("
            + str_percentage(num_files_without_filetags, number_of_files)
            + " of total files)"
        )

        print(
            "Number of files with filetags:                   "
            + str(num_files_with_filetags)
            + "   ("
            + str_percentage(num_files_with_filetags, number_of_files)
            + " of total files)"
        )

        top_10_tags = sorted(tag_dict.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]  # e.g.: [('v', 5), ('tag1', 4), ('tag4', 4)]
        if len(top_10_tags) > 0:
            print("\nTop 10 tags:")
            longest_tag = len(max([x[0] for x in top_10_tags], key=len))
            for item in top_10_tags:
                print(
                    "   {:<{}}  •  {:>{}} tagged file(s)   = {:>5} of tagged files".format(
                        item[0],
                        longest_tag,
                        item[1],
                        6,
                        str_percentage(item[1], num_files_with_alltags),
                    )
                )

        # FIX: Add controlled_vocabulary_filename back.
        if vocabulary:
            print(
                "\n\nYour controlled vocabulary is defined in "
                # + controlled_vocabulary_filename
                + " and contains "
                + str(len(vocabulary))
                + " tags.\n"
            )

            vocabulary_tags_not_used = set(vocabulary) - set(tag_dict.keys())
            if vocabulary_tags_not_used:
                print("\nTags from your vocabulary which you didn't use:\n")
                self.print_tag_set(vocabulary_tags_not_used)

            tags_not_in_vocabulary = set(tag_dict.keys()) - set(vocabulary)
            if tags_not_in_vocabulary:
                print("\nTags you used that are not in the vocabulary:\n")
                self.print_tag_set(tags_not_in_vocabulary)

            if self.nique_tags and len(self.nique_tags) > 0:
                # There are mutually exclusive tags defined in the controlled vocabulary
                for taggroup in self.unique_tags:
                    # iterate over mutually exclusive tag groups one by one

                    if taggroup == UNIQUE_TAG_TESTSTRINGS:
                        continue
                    if len(set(tag_dict.keys()).intersection(set(taggroup))) > 0:
                        files_with_any_tag_from_taggroup = [
                            x
                            for x in files_with_metadata
                            if len(set(x["alltags"]).intersection(set(taggroup))) > 0
                        ]
                        num_files_with_any_tag_from_taggroup = len(
                            files_with_any_tag_from_taggroup
                        )
                        print(
                            "\nTag group "
                            + str(taggroup)
                            + ":\n   Number of files with tag from tag group: "
                            + str(num_files_with_any_tag_from_taggroup)
                            + "   ("
                            + str_percentage(
                                num_files_with_any_tag_from_taggroup,
                                num_files_with_alltags,
                            )
                            + " of tagged files)"
                        )

                        longest_tagname = max(taggroup, key=len)
                        for tag in taggroup:
                            files_with_tag_from_taggroup = [
                                x for x in files_with_metadata if tag in x["alltags"]
                            ]
                            num_files_with_tag_from_taggroup = len(
                                files_with_tag_from_taggroup
                            )
                            if num_files_with_tag_from_taggroup > 0:
                                print(
                                    "   {:<{}}  •  {:>{}} tagged file(s)   = {:>5} of tag group".format(
                                        tag,
                                        len(longest_tagname),
                                        str(num_files_with_tag_from_taggroup),
                                        len(str(num_files_with_any_tag_from_taggroup)),
                                        str_percentage(
                                            num_files_with_tag_from_taggroup,
                                            num_files_with_any_tag_from_taggroup,
                                        ),
                                    )
                                )
                            else:
                                print('   "' + tag + '": Not used')
                    else:
                        print("\nTag group " + str(taggroup) + ": Not used")

        print(
            "\nTags that appear only once are most probably typos or you have forgotten them:"
        )
        tags_only_used_once_dict = {
            key: value for key, value in list(tag_dict.items()) if value < 2
        }
        self.print_tag_dict(
            tags_only_used_once_dict,
            vocabulary,
            sort_index=0,
            print_only_tags_with_similar_tags=False,
        )

        if vocabulary:
            print(
                "\nTags which have similar other tags are probably typos or plural/singular forms of others:\n  (first for tags not in vocabulary, second for vocaulary tags)"
            )
            tags_for_comparing = list(
                set(tag_dict.keys()).union(set(vocabulary))
            )  # unified elements of both lists
            only_similar_tags_by_alphabet_dict = {
                key: value
                for key, value in list(tag_dict.items())
                if self.find_similar_tags(key, tags_for_comparing)
            }

            self.print_tag_dict(
                {
                    key: value
                    for key, value in only_similar_tags_by_alphabet_dict.items()
                    if key not in vocabulary
                },
                vocabulary,
                sort_index=0,
                print_similar_vocabulary_tags=True,
            )
            self.print_tag_dict(
                {
                    key: value
                    for key, value in only_similar_tags_by_alphabet_dict.items()
                    if key in vocabulary
                },
                vocabulary,
                sort_index=0,
                print_similar_vocabulary_tags=True,
            )
        else:
            print(
                "\nTags which have similar other tags are probably typos or plural/singular forms of others:"
            )
            tags_for_comparing = list(set(tag_dict.keys()))
            only_similar_tags_by_alphabet_dict = {
                key: value
                for key, value in list(tag_dict.items())
                if self.find_similar_tags(key, tags_for_comparing)
            }
            self.print_tag_dict(
                only_similar_tags_by_alphabet_dict,
                vocabulary,
                sort_index=0,
                print_similar_vocabulary_tags=True,
            )

        tags_only_used_once_set = set(tags_only_used_once_dict.keys())
        only_similar_tags_by_alphabet_set = set(
            only_similar_tags_by_alphabet_dict.keys()
        )
        tags_in_both_outputs = tags_only_used_once_set.intersection(
            only_similar_tags_by_alphabet_set
        )

        if tags_in_both_outputs != set([]):
            print(
                "\nIf tags appear in both sections from above (only once and similar to "
                + "others), they most likely\nrequire your attention:"
            )
            self.print_tag_set(
                tags_in_both_outputs,
                vocabulary=vocabulary,
                print_similar_vocabulary_tags=True,
            )
