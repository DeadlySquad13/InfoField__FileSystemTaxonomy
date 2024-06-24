# REFACTOR: Move to data_structures and reuse here as a simple function call.
def add_tag_to_countdict(tag, tags):
    """
    Takes a tag (string) and a dict. Returns the dict with count value increased by one

    @param tag: a (unicode) string
    @param tags: dict of tags
    @param return: dict of tags with incremented counter of tag (or 0 if new)
    """

    assert tag.__class__ == str
    assert tags.__class__ == dict

    if tag in list(tags.keys()):
        tags[tag] = tags[tag] + 1
    else:
        tags[tag] = 1

    return tags
