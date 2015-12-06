from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath
from os      import listdir, sep, makedirs


HOME_DIRECTORY = '~'


def directory_listing_with_slahes(path):
    """
    Return directory listing with directories having trailing slashes.
    """
    output = []

    for filename in listdir(path):
        if isdir(join(path,filename)):
            output.append(filename + sep)
        else:
            output.append(filename)

    return output


def get_current_directory(view_filename, folders, use_project_dir):
    """
    Try to give a sensible estimate for 'current directory'.
    If there is a single folder open, we return that.
    Else, if there is an active file, return its path.
    If all else fails, return the home directory.
    """
    if folders and use_project_dir:
        directory = folders[0]
    elif view_filename is not None:
        directory, _ = split(view_filename)
    else:
        directory = HOME_DIRECTORY

    if directory != sep:
        directory += sep

    return get_path_relative_to_home(directory)


def get_path_relative_to_home(path):
    home = expanduser(HOME_DIRECTORY)

    if len(commonprefix([home, path])) > 1:
        relative_path = relpath(path, home)
        if len(relative_path) > 1:
            return join(HOME_DIRECTORY, relpath(path, home)) + sep
        else:
            return HOME_DIRECTORY + sep
    else:
        return path
