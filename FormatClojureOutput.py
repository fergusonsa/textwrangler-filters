#!/usr/bin/python
import fileinput


def parse_clojurelojure(text):
    parsed_text = []
    for line in text:
        line.strip();

    return parsed_text


def parse_dict(text):
    pass


def parse_set(text):
    pass


def parse_list(text):
    pass


def print(parsed_text):
    pass


def load_all_text(file_handle):
    text = ''
    for line in fileinput.input():
        text = text + ' ' + line.strip()
    return text


if __name__ == "__main__":
    original_lines = []
    for line in fileinput.input():
        string_to_format = string_to_format + ' ' + line.strip()
        original_lines.append(line)

    try:
        parsed_text = parse_clojure(all_text)

    except:
        for line in original_lines:
            print line,
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
