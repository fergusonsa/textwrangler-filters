#!/usr/bin/python
from __future__ import print_function
import fileinput
import os.path
import datetime

if __name__ == "__main__":
    todays_date_str = datetime.date.today().isoformat()
    update_input = True
    expected_filename = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                                     'notes',
                                                     '{}.txt'.format(todays_date_str)))

    if not os.path.exists(expected_filename):
        with open(expected_filename, mode='w') as newfile:
            newfile.write('{:<24}Arrived and logged in\n'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M %p')))
        os.system('open {}'.format(expected_filename))
        update_input = False

    last_line = ''
    for line in fileinput.input():
        last_line = line
        if fileinput.isfirstline():
            # Check the start of the first line to make sure that it has today's date
            update_input = line.startswith(todays_date_str)
        print(line, end='')
    if update_input:
        if not last_line.endswith(os.linesep):
            print('')
        print('{:<24}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M %p')), end='')
