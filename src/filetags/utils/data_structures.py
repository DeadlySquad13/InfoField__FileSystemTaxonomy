import os
import colorama  # for colorful output

from filetags.cli import TTY_WIDTH


def item_contained_in_list_of_lists(item, list_of_lists):
    """
    Returns true if item is member of at least one list in list_of_lists.

    @param item: item too look for in list_of_lists
    @param list_of_lists: list containing a list of items
    @param return: (item, list) or None
    """

    for current_list in list_of_lists:
        if item in current_list:
            return item, current_list
    return None, None


# REFACTOR: one part to the cli, transition detection part stay leave here.
def print_item_transition(path, source, destination, transition, max_file_length):
    """
    Returns true if item is member of at least one list in list_of_lists.

    @param path: string containing the path to the files
    @param source: string of basename of filename before transition
    @param destination: string of basename of filename after transition or target
    @param transision: string which determines type of transision: ("add", "delete", "link")
    @param return: N/A
    """

    transition_description = ""
    if transition == "add":
        transition_description = "renaming"
    elif transition == "delete":
        transition_description = "renaming"
    elif transition == "link":
        transition_description = "linking"
    else:
        print(
            'ERROR: print_item_transition(): unknown transition parameter: "'
            + transition
            + '"'
        )

    style_destination = (
        colorama.Style.BRIGHT + colorama.Back.GREEN + colorama.Fore.BLACK
    )
    destination = (
        style_destination + os.path.basename(destination) + colorama.Style.RESET_ALL
    )

    if 15 + len(transition_description) + (2 * max_file_length) < TTY_WIDTH:
        # probably enough space: screen output with one item per line

        source_width = max_file_length

        source = source
        arrow_left = colorama.Style.DIM + "――"
        arrow_right = "―→"
        print(
            "  {0:<{width}s}   {1:s}{2:s}{3:s}   {4:s}".format(
                source,
                arrow_left,
                transition_description,
                arrow_right,
                destination,
                width=source_width,
            )
        )

    else:
        # for narrow screens (and long file names): split up item source/destination in two lines

        print(
            ' {0:<{width}s}  "{1:s}"'.format(
                transition_description, source, width=len(transition_description)
            )
        )
        print(
            ' {0:<{width}s}     ⤷   "{1:s}"'.format(
                " ", destination, width=len(transition_description)
            )
        )
