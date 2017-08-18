#!/usr/bin/python
from __future__ import print_function
import fileinput
import json
import sys

def get_string_to_format():
    json_string = ''
    original_lines = []
    for line in fileinput.input():
        json_string = json_string + ' ' + line.strip()
        original_lines.append(line)
    return original_lines, json_string

if __name__ == "__main__":

    original_lines, json_string = get_string_to_format()

    try:
        remove_extra_braces = False
        try:
            json_object = json.loads(json_string.encode('utf-8'))
        except:
            json_object = json.loads('{%s}'%(json_string).encode('utf-8'))
            remove_extra_braces = True

        new_json_str = json.dumps(json_object, sort_keys=True, indent=2).encode('utf-8')
        if remove_extra_braces:
            print(new_json_str[1:-1], end='')
        else:
            print(new_json_str, end='')
    except:
        for line in original_lines:
            print(line, end='')
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
