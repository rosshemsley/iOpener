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


def get_path_to_home():
    return HOME_DIRECTORY + sep


def get_path_relative_to_home(path):
    home = expanduser(HOME_DIRECTORY)

    if len(commonprefix([home, path])) > 1:
        relative_path = relpath(path, home)
        if len(relative_path) > 1:
            return join(HOME_DIRECTORY, relpath(path, home)) + sep
        else:
            return HOME_DIRECTORY + sep

    elif path.endswith(sep):
        return path

    else:
        return path + sep
