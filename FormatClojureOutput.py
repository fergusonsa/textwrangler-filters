#!/usr/bin/python
from __future__ import print_function

import fileinput
import sys

INDENT_STRING = '  '

# SEQUENCE_STARTING_CHARS = ['{', '[', '(']
SEQUENCE_CHARS = {'{':'}',
                  '[':']',
                  '(':')'}

SEQUENCE_STARTING_CHARS = SEQUENCE_CHARS.keys()

class Holder:
    input_string = ''
    index = -1
    length = 0
    def __init__(self, input_string):
        self.input_string = input_string
        self.length = len(self.input_string)


    def get_ch(self):
        if (self.index + 1) < self.length:
            self.index += 1
            ch = self.input_string[self.index]
#             print('get_ch: ch {} index {}'.format(ch, self.index), end='')
            return ch
        else:
#             print('get_ch: Past end of string! index {} length {}'.format(self.index, self.length), end='')
            return None


    def see_next_ch(self):
        if (self.index + 1) < self.length:
            return self.input_string[self.index + 1]
        else:
            return None

    def does_next_ch_starts_seq(self):
        return self.see_next_ch() in SEQUENCE_STARTING_CHARS

def get_sequence_ending_ch(starting_ch):
    return SEQUENCE_CHARS[starting_ch]


def skip_white_space(holder):
    while holder.see_next_ch() in [' ', '\n', '\t']:
        holder.get_ch()


def print_formatted_clojure(holder, indent=0, end_ch=None):
#     print('p_f_c(holder, {}, {})'.format(indent, end_ch), end='')
    ch = holder.get_ch()
    if ch and not holder.does_next_ch_starts_seq():
        print(INDENT_STRING*indent, end='')
    while ch and ch != end_ch:
        if ch == ',':
            print(ch)
            print(INDENT_STRING*indent, end='')
            skip_white_space(holder)
        elif ch in SEQUENCE_STARTING_CHARS:
            print()
            print(INDENT_STRING*(indent+1), end='')
            print(ch, end='' if holder.does_next_ch_starts_seq() else '\n')
            skip_white_space(holder)
            index = print_formatted_clojure(holder, indent+1 if holder.does_next_ch_starts_seq() else indent+2, get_sequence_ending_ch(ch))
            print(get_sequence_ending_ch(ch), end='')
        else:
            print(ch, end='')
        ch = holder.get_ch()


def format_clojure_main(string_to_format):
    holder = Holder(string_to_format)
    print_formatted_clojure(holder, -1)
    print()

if __name__ == "__main__":
    original_lines = []
    string_to_format = ''
    for line in fileinput.input():
        string_to_format = string_to_format + ' ' + line.strip()
        original_lines.append(line)

    try:
        format_clojure_main(string_to_format)
    except:
        for line in original_lines:
            print(line, end='')
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
