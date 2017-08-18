#!/usr/bin/python
from __future__ import print_function
import fileinput
import os
import os.path
import shutil
import sqlite3
import tempfile
import datetime


def find_path():
    file_path = os.path.join( os.environ.get("HOME"), 'Library', 'Application Support', 'Google', 'Chrome', 'Profile 1', 'History')
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(file_path, temp_path)
    return temp_path


def cleanup(file_path):
    shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)


def get_chrome_history():

    history_file_path = find_path()
    allrows = None
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    try:
        con = sqlite3.connect(find_path()) #Connect to the database
        con.text_factory = str
        c = con.cursor()

        rows = c.execute('select datetime(last_visit_time/1000000-11644473600,"unixepoch"),title, url from urls where datetime(last_visit_time/1000000-11644473600,"unixepoch") >= datetime("' + today_str + 'T00:00") order by last_visit_time desc')
        allrows = rows.fetchall()
        con.close()
    finally:
        cleanup(history_file_path)
    return allrows


if __name__ == "__main__":
    todays_date_str = datetime.date.today().isoformat()
    update_input = True
    expected_filename = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                                     'notes',
                                                     '{}.txt'.format(todays_date_str)))

    if not os.path.exists(expected_filename):
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
        print('{:<24} Leaving for the day\n\n'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M %p')), end='')
        print('\nToday''s Chrome history:\n==============================\n')
        for row in get_chrome_history():
            print('{0[0]}  {0[1]:70}  {0[2]}'.format(row))
        print('\n==============================\n')

