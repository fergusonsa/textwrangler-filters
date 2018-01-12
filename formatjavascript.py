#!/usr/bin/python
from __future__ import print_function
import jsbeautifier
import fileinput

if __name__ == "__main__":
    original_lines = []
    string_to_format = ''
    for line in fileinput.input():
        string_to_format = string_to_format + ' ' + line.strip()
        original_lines.append(line)

    try:
        res = jsbeautifier.beautify(string_to_format)
        print()
        print(res)
    except:
        for line in original_lines:
            print(line, end='')
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
