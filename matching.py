from unittest import TestCase

from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath
from os      import listdir, sep, makedirs

def complete_path(filename, directory, matches):
    # If this match is not unique.
    if len(matches) >  1:
        # We can do this more efficiently later.
        # Get the longest prefix, ignoring case.
        prefix_length = len( commonprefix([ s.lower() for s in matches ]) )
        new_filename  = filename + matches[0][len(filename):prefix_length]
        status        = "Complete, but not unique"
        completed     = False

        return new_filename, status, completed
    elif len(matches) == 1:
        new_filename  = matches[0]
        # If we completed a directory
        if isdir(expanduser(join(directory, new_filename))):
            new_filename += sep
        status        = None
        completed     = True
        return new_filename, status, completed
    else:
        new_filename  = filename
        status        = "No match"
        completed     = False
        return new_filename, status, completed


def get_matches(filename, directory_listing, case_sensitive):
    if case_sensitive:
        return [f for f in directory_listing if f.startswith(filename)]
    else:
        return [f for f in directory_listing if f.lower().startswith(filename.lower())]


##
# Unit tests
##


class TestMatches(TestCase):
    def test1(self):
        directory_listing = [
            'filename',
            'filen',
            'fi',
            'Filename',
        ]

        output = get_matches('file', directory_listing, case_sensitive=True)
        expected = [
            'filename',
            'filen',
        ]

        self.assertListEqual(expected, output)

    def test2(self):
        directory_listing = [
            'filename',
            'filen',
            'fi',
            'Filename',
        ]

        output = get_matches('file', directory_listing, case_sensitive=False)
        expected = [
            'filename',
            'filen',
            'Filename',
        ]

        self.assertListEqual(expected, output)

    def test3(self):
        directory_listing = ['test']
        output = get_matches('', directory_listing, case_sensitive=True)
        self.assertListEqual(['test'], output)
