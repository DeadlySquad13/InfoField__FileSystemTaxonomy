from filetags.cli.parser.options import CliOptions
from filetags.utils.logging import error_exit


def validate_options(options: CliOptions):
    if options.verbose and options.quiet:
        error_exit(
            1,
            'Options "--verbose" and "--quiet" found. '
            + "This does not make any sense, you silly fool :-)",
        )

    # Interactive mode and tags are given.
    if options.interactive and options.tags:
        error_exit(
            3,
            'I found option "--tag" and option "--interactive". \n'
            + "Please choose either tag option OR interactive mode.",
        )

    if options.list_tags_by_number and options.list_tags_by_alphabet:
        error_exit(6, "Please use only one list-by-option at once.")

    if options.tag_gardening and (
        options.list_tags_by_number
        or options.list_tags_by_alphabet
        or options.tags
        or options.tagtrees
        or options.tagfilter
    ):
        error_exit(
            7, "Please don't use that gardening option together with any other option."
        )

    if options.tagfilter and (
        options.list_tags_by_number
        or options.list_tags_by_alphabet
        or options.tags
        or options.tag_gardening
    ):
        error_exit(
            14, "Please don't use that filter option together with any other option."
        )

    if options.list_tags_by_number and (
        options.tagfilter
        or options.list_tags_by_alphabet
        or options.tags
        or options.tagtrees
        or options.tag_gardening
    ):
        error_exit(
            15, "Please don't use that list option together with any other option."
        )

    if options.list_tags_by_alphabet and (
        options.tagfilter
        or options.list_tags_by_number
        or options.tags
        or options.tagtrees
        or options.tag_gardening
    ):
        error_exit(
            16, "Please don't use that list option together with any other option."
        )

    if options.tags and (
        options.tagfilter
        or options.list_tags_by_number
        or options.list_tags_by_alphabet
        or options.tagtrees
        or options.tag_gardening
    ):
        error_exit(
            17, "Please don't use that tags option together with any other option."
        )

    if options.tagtrees and (
        options.list_tags_by_number
        or options.list_tags_by_alphabet
        or options.tags
        or options.tag_gardening
    ):
        error_exit(
            18, "Please don't use the tagtrees option together with any other option."
        )

    if (options.list_tags_by_alphabet or options.list_tags_by_number) and (
        options.tags or options.interactive or options.remove
    ):
        error_exit(
            8, "Please don't use list any option together with add/remove tag options."
        )
