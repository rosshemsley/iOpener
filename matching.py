from unittest import TestCase

from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath
from os      import listdir, sep, makedirs


def get_directory_listing(path):
    """
    Return directory listing with directories annotated.
    """
    output = []

    for filename in listdir(path):
        if isdir(join(path,filename)):
            output.append(filename + sep)
        else:
            output.append(filename)

    return output


def complete_path(filename, directory_listing, case_sensitive=False):
    matches = get_matches(filename, directory_listing, case_sensitive)

    if len(matches) > 1:
        new_filename  = longest_completion(filename, matches)
        status        = "Complete, but not unique"
        completed     = False
    elif len(matches) == 1:
        status = None
        completed = True
        new_filename = matches[0]
    else:
        new_filename  = filename
        status = "No match"
        completed = False

    return new_filename, status, completed


def get_matches(filename, directory_listing, case_sensitive):
    if case_sensitive:
        return [f for f in directory_listing if f.startswith(filename)]
    else:
        return [f for f in directory_listing if f.lower().startswith(filename.lower())]


def longest_completion(filename, matches):
    return filename + commonprefix(matches)[len(filename):]


##
# Unit tests
##


class TestCompletion(TestCase):
    def test1(self):
        filename = 'test'
        matches = [
            'testable',
            'testa',
            'testand',
            'testand'
        ]
        output = longest_completion(filename, matches)
        expected = 'testa'

        self.assertEqual(expected, output)

    def test2(self):
        filename = 'test'
        matches = [
            'testable',
            'testa',
            'testand',
            'Testand'
        ]
        output = longest_completion(filename, matches)
        expected = 'test'

        self.assertEqual(expected, output)

    def test3(self):
        filename = 'test'
        matches = [
            'tester',
            'testable',
            'testa',
            'testand',
            'Testand'
        ]
        output = longest_completion(filename, matches)
        expected = 'test'

        self.assertEqual(expected, output)


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
