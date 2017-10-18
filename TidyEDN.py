#!/usr/bin/python
import fileinput
import edn_format
import edn_format.edn_lex as edn_lex
import edn_format.edn_parse as edn_parse
import edn_format.edn_dump as edn_dump
import edn_format.immutable_dict
import re
import sys
import pprint
import pyrfc3339
import datetime
import decimal
import itertools


class BaseClass(edn_format.TaggedElement):
    def __init__(self, classtype):
        self._type = classtype

def ClassFactory(name, fqn_name, argnames=[], BaseClass=BaseClass):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # here, the argnames variable is the one passed to the
            # ClassFactory call
            if key not in argnames:
                raise TypeError("Argument %s not valid for %s"
                    % (key, self.__class__.__name__))
            setattr(self, key, value)
        BaseClass.__init__(self, fqn_name, name[:-len("Class")])
    newclass = type(name, (BaseClass,),{"__init__": __init__})
    return newclass


def subclass_init(self, value):
    super(self.__class__, self).__init__()
    print('subclass_init() for %s with value %s' % (self.__class__.__name__, value))
    if isinstance(value, basestring) and value.startswith('{'):
        self.value = edn_format.loads(value)
    else:
        self.value = value


def subclass__str__(self):
    if isinstance(self.value, basestring):
        val_str = self.value
    else:
        val_str = edn_format.dumps(self.value, sort_keys=True).encode('utf-8')
    return '#{} {}\n'.format(
        self.name,
        val_str)


def print_class(obj,
              indent=0,
              string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
              keyword_keys=False,
              sort_keys=False):
    pass

def format_map_entrys(pairs,
                      indent=0,
                      string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
                      keyword_keys=False,
                      sort_keys=False):
    indent_str = '\n{}'.format(' ' * (4*indent))
    if len(pairs) > 1:
        return indent_str.join('{}'.format(edn_dump.seq(itertools.chain.from_iterable(pairs), **{
#                 "indent": indent + 1,
                "string_encoding": string_encoding,
                "keyword_keys": keyword_keys,
                "sort_keys": sort_keys,})))

    else:
        return '{}\n'.format(edn_dump.seq(obj, **{
#             "indent": indent,
            "string_encoding": string_encoding,
            "keyword_keys": keyword_keys,
            "sort_keys": sort_keys,}))

def print_map(obj,
              indent=0,
              string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
              keyword_keys=False,
              sort_keys=False):
    indent = indent + 1
    pairs = obj.items()
    if sort_keys:
        pairs = sorted(pairs, key=lambda p: str(p[0]))
    if keyword_keys:
        pairs = ((edn_lex.Keyword(k) if isinstance(k, (bytes, basestring)) else k, v) for k, v in pairs)

    breaker = '\n' if len(pairs) > 1 else ""
    print('{{{}{}}}'.format(breaker, format_map_entrys(pairs, **{
        "indent": indent,
        "string_encoding": string_encoding,
        "keyword_keys": keyword_keys,
        "sort_keys": sort_keys,})))

def print_list(obj,
              indent=0,
              string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
              keyword_keys=False,
              sort_keys=False):
    print('({})'.format(edn_dump.seq(obj, **{
#         "indent": indent,
        "string_encoding": string_encoding,
        "keyword_keys": keyword_keys,
        "sort_keys": sort_keys,
    })))

def print_vector(obj,
               indent=0,
               string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
               keyword_keys=False,
               sort_keys=False):
    print('[{}]'.format(edn_dump.seq(obj, **{
#         "indent": indent,
        "string_encoding": string_encoding,
        "keyword_keys": keyword_keys,
        "sort_keys": sort_keys,
    })))


def print_set(obj,
              indent=0,
              string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
              keyword_keys=False,
              sort_keys=False):
    print('#{{\n{}}}'.format(edn_dump.seq(obj, **{
#         "indent": indent,
        "string_encoding": string_encoding,
        "keyword_keys": keyword_keys,
        "sort_keys": sort_keys,
    })))

def print_edn(obj,
              indent=0,
              string_encoding=edn_dump.DEFAULT_INPUT_ENCODING,
              keyword_keys=False,
              sort_keys=False):

    kwargs = {
        "string_encoding": string_encoding,
        "keyword_keys": keyword_keys,
        "sort_keys": sort_keys,
    }

    if obj is None:
        print('nil')
    elif isinstance(obj, bool):
        print('true' if obj else 'false')
    elif isinstance(obj, (int, long, float)):
        print(unicode(obj))
    elif isinstance(obj, decimal.Decimal):
        print('{}M'.format(obj))
    elif isinstance(obj, (edn_lex.Keyword, edn_lex.Symbol)):
        print(unicode(obj))
    # CAVEAT EMPTOR! In Python 3 'basestring' is alised to 'str' above.
    # Furthermore, in Python 2 bytes is an instance of 'str'/'basestring' while
    # in Python 3 it is not.
    elif isinstance(obj, bytes):
        print(edn_dump.unicode_escape(obj.decode(string_encoding)))
    elif isinstance(obj, basestring):
        print(edn_dump.unicode_escape(obj))
    elif isinstance(obj, tuple):
        print_list(obj, indent, string_encoding, keyword_keys, sort_keys)
    elif isinstance(obj, list):
        print_vector(obj, indent, string_encoding, keyword_keys, sort_keys)
    elif isinstance(obj, set) or isinstance(obj, frozenset):
        print_set(obj, indent, string_encoding, keyword_keys, sort_keys)
    elif isinstance(obj, dict) or isinstance(obj, edn_format.immutable_dict.ImmutableDict):
        print_map(obj, indent, string_encoding, keyword_keys, sort_keys)
    elif isinstance(obj, datetime.datetime):
        print('#inst "{}"'.format(pyrfc3339.generate(obj, microseconds=True)))
    elif isinstance(obj, datetime.date):
        print('#inst "{}"'.format(obj.isoformat()))
    elif isinstance(obj, uuid.UUID):
        print('#uuid "{}"'.format(obj))
    elif isinstance(obj, edn_parse.TaggedElement):
        print(unicode(obj))
    else:
        raise NotImplementedError(
            u"encountered object of type '{}' for which no known encoding is available: {}".format(
                type(obj), repr(obj)))

def get_edn_obj_from_string(string_of_edn):
    # Find out all the names of the classes that are present in the string to format
    set_of_classes = set(re.findall(r"#([a-zA-Z][a-zA-Z0-9\.\-]*)[\s]*[{\[]", string_of_edn))
    for class_name in set_of_classes:
        fqn_name = class_name
        new_class_name = fqn_name.replace('.', '_') + 'Class'
        print('Creating class for %s with name %s and from original found text %s' % (fqn_name, new_class_name, class_name))
        SpecialClass = type(new_class_name, (edn_format.TaggedElement,), {'name': fqn_name, '__init__': subclass_init, '__str__': subclass__str__})
        edn_format.add_tag(fqn_name, SpecialClass)
    return edn_format.loads(string_of_edn.encode('utf-8'))


def print_edn_format(string_to_format):
    new_object = get_edn_obj_from_string(string_to_format)
    print('-----done------')
    print(edn_format.dumps(new_object, sort_keys=True).encode('utf-8'))
    print('-----print------')
    print_edn(new_object)
    print('-----------')

def load_file(path):
    contents = ""
    file = open(path, 'r')
    for line in file:
        clean_line = line.strip()
        if not clean_line.startswith(';'):
            contents = contents + ' ' + clean_line
    return  contents


if __name__ == "__main__":
    string_to_format = ''
    original_lines = []
    for line in fileinput.input():
        string_to_format = string_to_format + ' ' + line.strip()
        original_lines.append(line)

    try:

        print_edn_format(string_to_format)

    except:
        for line in original_lines:
            print line,
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
