from filetags.consts import (BETWEEN_TAG_SEPARATOR, FILENAME_TAG_SEPARATOR,
                             PROG_VERSION_DATE)

DESCRIPTION = (
    'This tool adds or removes simple tags to/from file names.\n\
\n\
Tags within file names are placed between the actual file name and\n\
the file extension, separated with "'
    + FILENAME_TAG_SEPARATOR
    + '". Multiple tags are\n\
separated with "'
    + BETWEEN_TAG_SEPARATOR
    + '":\n\
  Update for the Boss'
    + FILENAME_TAG_SEPARATOR
    + "projectA"
    + BETWEEN_TAG_SEPARATOR
    + "presentation.pptx\n\
  2013-05-16T15.31.42 Error message"
    + FILENAME_TAG_SEPARATOR
    + "screenshot"
    + BETWEEN_TAG_SEPARATOR
    + 'projectB.png\n\
\n\
This easy to use tag system has a drawback: for tagging a larger\n\
set of files with the same tag, you have to rename each file\n\
separately. With this tool, this only requires one step.\n\
\n\
Example usages:\n\
  filetags --tags="presentation projectA" *.pptx\n\
      … adds the tags "presentation" and "projectA" to all PPTX-files\n\
  filetags --tags="presentation -projectA" *.pptx\n\
      … adds the tag "presentation" to and removes tag "projectA" from all PPTX-files\n\
  filetags -i *\n\
      … ask for tag(s) and add them to all files in current folder\n\
  filetags -r draft *report*\n\
      … removes the tag "draft" from all files containing the word "report"\n\
\n\
\n\
This tools is looking for the optional first text file named ".filetags" in\n\
current and parent directories. Each of its lines is interpreted as a tag\n\
for tag completion. Multiple tags per line are considered mutual exclusive.\n\
\n\
Verbose description: http://Karl-Voit.at/managing-digital-photographs/'
)

EPILOG = (
    "\n\
:copyright: (c) by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/filetags\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: "
    + PROG_VERSION_DATE
    + "\n·\n"
)
