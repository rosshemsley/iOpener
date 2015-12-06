from unittest import TestCase

from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath
from os      import listdir, sep, makedirs


class COMPLETION_TYPE:
    CompleteButNotUnique = 0
    Complete = 1
    NoMatch = 2


def complete_path(filename, directory_listing, case_sensitive=False):
    matches = get_matches(filename, directory_listing, case_sensitive)

    if len(matches) > 1:
        new_filename = longest_completion(filename, matches)
        return new_filename, COMPLETION_TYPE.CompleteButNotUnique

    elif len(matches) == 1:
        return matches[0], COMPLETION_TYPE.Complete
    else:
        return filename, COMPLETION_TYPE.NoMatch


def get_matches(filename, directory_listing, case_sensitive):
    if case_sensitive:
        return [f for f in directory_listing if f.startswith(filename)]
    else:
        return [f for f in directory_listing if f.lower().startswith(filename.lower())]


def longest_completion(filename, matches):
    return filename + commonprefix(matches)[len(filename):]


def lcs(A, B):
    """
    Taken and adapted from
    http://rosettacode.org/wiki/Longest_common_subsequence#Dynamic_Programming_7
    """
    lengths = [[0 for j in range(len(B) + 1)] for i in range(len(A) + 1)]

    for i, x in enumerate(A):
        for j, y in enumerate(B):
            if x == y:
                lengths[i + 1][j + 1] = lengths[i][j] + 1
            else:
                lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])

    result = ""
    x, y = len(A), len(B)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            result = A[x-1] + result
            x -= 1
            y -= 1
    return result


##
# Unit tests
##


class TestLCS(TestCase):
    def test1(self):
        self.assertEqual('hel', lcs('hello', 'heal'))
        self.assertEqual('oe', lcs('hope', 'oe'))
        self.assertEqual('', lcs('this', 'xyz'))
        self.assertEqual('bcd', lcs('abcdefg', 'bcd'))
        self.assertEqual('test', lcs('test', 'test'))
        self.assertEqual('rd', lcs('read', 'rd'))
        self.assertEqual('round', lcs('round', 'arounded'))


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
