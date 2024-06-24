# Filetags
## Architecture
Process of the module is following:
1. Simple file operations (checking validity, existance... )
2. Tag related file operations (getting tags from filenames, removing them...)
3. Storing obtained data from previous steps
4. Creating a tagtree
5. Integration: show in different app

Also there's a tag gardening which is a beast on it's own: it's out of common
flow. Of course it uses parts from previous steps.

1st can be abstracted as a simple wrappers around `os` and `pathlib` modules.
2nd and 3rd should be made as a class `Tags` that uses functions from first and
updates storage on every operation.
4th should be made as an interpreter of the class `Tags`

`Tags` class should handle both Windows and Unix platforms. Maybe in the future
it will be abstracted even further to work with virtual systems like email and
network. Taking this and the fact that file operations are already a separate
module into account, we should made `Tags` expect a service that will handle
all the dirty work. This way `Tags` will handle only tag related operations and
use very abstract operations of the service.
