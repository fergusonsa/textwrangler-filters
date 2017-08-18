#!/usr/bin/python
import fileinput
import edn_format
import re
import sys


class TagOptionalKey(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagOptionalKey, self).__init__()
                self.name = 'schema.core.OptionalKey'
                self.key = ''
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
#                     self.key,
                    self.value)

class TagOne(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagOne, self).__init__()
                self.name = 'schema.core.One'
                self.key = ''
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
#                     self.key,
                    self.value)

class TagWebServer(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagWebServer, self).__init__()
                self.name = 'cenx.mercury.servers.web.WebServer'
                self.key = ''
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
#                     self.key,
                    self.value)

class TagWebSocketServer(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagWebSocketServer, self).__init__()
                self.name = 'cenx.mercury.servers.web.WebSocketServer'
                self.key = ''
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
#                     self.key,
                    self.value)

class TagObject(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagObject, self).__init__()
                self.name = 'object'
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
                    self.value)

class TagPolar(edn_format.TaggedElement):
            def __init__(self, value):
                super(TagPolar, self).__init__()
                self.name = 'Polar'
                self.value = value

            def __str__(self):
                return '#{} {}'.format(
                    self.name,
                    self.value)

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


if __name__ == "__main__":
    string_to_format = ''
    original_lines = []
    for line in fileinput.input():
        string_to_format = string_to_format + ' ' + line.strip()
        original_lines.append(line)

    try:
        # Find out all the names of the classes that are present in the string to format
        set_of_classes = set(re.findall(r"#([a-zA-Z][a-zA-Z0-9\.\-]*)[\s]*[{\[]", string_to_format))
        for class_name in set_of_classes:
            fqn_name = class_name
            new_class_name = fqn_name.replace('.', '_') + 'Class'
            print('Creating class for %s with name %s and from original found text %s' % (fqn_name, new_class_name, class_name))
            SpecialClass = type(new_class_name, (edn_format.TaggedElement,), {'name': fqn_name, '__init__': subclass_init, '__str__': subclass__str__})
#             SpecialClass = ClassFactory(new_class_name, fqn_name, ['value'])
            edn_format.add_tag(fqn_name, SpecialClass)
#         edn_format.add_tag('schema.core.OptionalKey', TagOptionalKey)
#         edn_format.add_tag('schema.core.One', TagOne)
#         edn_format.add_tag('cenx.mercury.servers.web.WebServer', TagWebServer)
#         edn_format.add_tag('cenx.mercury.servers.websocket.WebSocketServer', TagWebSocketServer)
#         edn_format.add_tag('object', TagObject)
#         edn_format.add_tag('cenx.polar.services.Polar', TagPolar)
        new_object = edn_format.loads(string_to_format.encode('utf-8'))
        print('-----------')
        print(edn_format.dumps(new_object, sort_keys=True).encode('utf-8'))
    except:
        for line in original_lines:
            print line,
        e = sys.exc_info()

        print('\nEXCEPTION HAPPENED! %s \n%s \n%s' % (e[0], e[1], e[2]))
