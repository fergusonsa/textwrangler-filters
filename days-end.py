#!/usr/bin/python
from __future__ import print_function
import datetime
import fileinput
import os
import os.path
import re
import shutil
import sqlite3
import subprocess
import tempfile

DATE_TIME_FORMAT = '%Y-%m-%d %H:%M %p'
OUTPUT_FORMAT = "{:19}  {:15}  {}"
"""The pattern for lines output in the format of:
<timestamp>        <source>       <description of actionm>"""

BASH_HISTORY_INPUT_PATTERN = re.compile("^([^ ]*)\s*(\"[^\"]*\")?\s*([0-9]*)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)$")
""" The regex pattern for the bash history file input lines, in the expected format of:
<TTY> "<current-directory>" <history #> YYYY-mm-dd HH:MM:SS <bash command>

So group(1) == TTY
   group(2) == Current working directory when command is performed, surrounded by \"\"
   group(3) == bash history number
   group(4) == timestamp
   group(5) == bash command"""

UTILS_ACTION_INPUT_PATTERN = re.compile("^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)(\n?)$")
NOTE_FILENAME_PATTERN = re.compile("^(\d{4})-(\d{2})-(\d{2})\.txt$")
NOTE_FILE_LINE_PATTERN = re.compile("^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(:(\d{2})| [AP]M)\s*(.*)$")

def find_path():
    file_path = os.path.join( os.environ.get("HOME"), 'Library', 'Application Support', 'Google', 'Chrome', 'Profile 1', 'History')
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(file_path, temp_path)
    return temp_path


def cleanup(file_path):
    shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)


def get_utils_actions(for_date=datetime.date.today()):
    """
    Check for utils action log file for desired date.
    If present, return its contents
    """
    date_str = for_date.strftime('%Y%m%d')
    path = os.path.join(os.environ.get("HOME"), "reports", "action-logs", "action-log-{}.txt".format(date_str))
    if os.path.isfile(path):
        file = open(path, 'r')
        res_lines = []
        for line in file.readlines():
            matches = UTILS_ACTION_INPUT_PATTERN.match(line)
            res_lines.append(OUTPUT_FORMAT.format(matches.group(1), "Utils Action", matches.group(2)))
        return res_lines
    else:
        return []


def get_chrome_history(for_date=datetime.date.today()):

    history_file_path = find_path()
    allrows = None
    date_str = for_date.strftime('%Y-%m-%d')
    try:
        con = sqlite3.connect(find_path()) #Connect to the database
        con.text_factory = str
        c = con.cursor()

        rows = c.execute('select datetime(last_visit_time/1000000-11644473600, "unixepoch", "localtime"),title, url from urls where datetime(last_visit_time/1000000-11644473600,"unixepoch", "localtime") >= datetime("' + date_str + 'T00:00") order by last_visit_time desc')
        allrows = rows.fetchall()
        con.close()
    finally:
        cleanup(history_file_path)
    res_lines = []
    for line in allrows:
        res_lines.append(OUTPUT_FORMAT.format(line[0], "Chrome", line[1] + ' ' + line[2]))
    return res_lines


def get_bash_history2(for_date=datetime.date.today()):
    res_lines = []
    date_str = for_date.strftime('%Y-%m-%d')
    path = os.path.join(os.environ.get("HOME"), "reports", "bash_history", "bash_history-{}.txt".format(date_str))
    if os.path.isfile(path):
        file = open(path, 'r')
        for line in file.readlines():
            matches = BASH_HISTORY_INPUT_PATTERN.match(line)
            if matches:
                res_lines.append(OUTPUT_FORMAT.format(matches.group(4), "bash", matches.group(1) + " " + matches.group(2) + " " + matches.group(5)))

    return list(set(res_lines))


def get_todays_file_path(todays_date_str=datetime.date.today().isoformat()):
    return os.path.abspath(os.path.join(os.path.expanduser('~'),
                                        'notes',
                                        '{}.txt'.format(todays_date_str)))


def skip_existing_contents(expected_filename, todays_date_str, previous_date):
    if not os.path.exists(expected_filename):
        update_input = False

    last_line = ''
    for line in fileinput.input():
        last_line = line
        if fileinput.isfirstline():
            # Check the start of the first line to make sure that it has today's date
            update_input = line.startswith(todays_date_str)
            is_yesterdays_file = line.startswith(previous_date.isoformat())

        print(line, end='')
    return update_input, is_yesterdays_file, last_line


def get_fridays_date(todays_date=datetime.date.today()):
    target_dayofweek = 4  # Friday
    current_dayofweek = todays_date.weekday() # Today

    if target_dayofweek <= current_dayofweek:
        # target is in the current week
        return todays_date - datetime.timedelta(days=(current_dayofweek - target_dayofweek))

    else:
        # target is in the previous week
        return todays_date - datetime.timedelta(weeks=1) + datetime.timedelta(days=(target_dayofweek - current_dayofweek))


def is_filename_between_dates(file_path, start_date, end_date):
    parts = NOTE_FILENAME_PATTERN.match(os.path.basename(file_path))
    return parts and start_date <= datetime.datetime(int(parts.group(1)), int(parts.group(2)), int(parts.group(3))) <= end_date


def get_file_history(file_path):
    file_date = datetime.datetime.strptime(os.path.splitext(os.path.basename(file_path))[0], '%Y-%m-%d')
    first_timestamp = last_timestamp = timestamp = None
    with open(file_path, 'r') as flh:
        # Get the first and last times for entries in the file.
        for line in flh.readlines():
            parts = NOTE_FILE_LINE_PATTERN.match(line)
            if parts:
                timestamp = datetime.datetime(int(parts.group(1)), int(parts.group(2)), int(parts.group(3)),
                                              int(parts.group(4)), int(parts.group(5)))
                if (not first_timestamp or timestamp < first_timestamp) and timestamp > file_date:
                    first_timestamp = timestamp
                elif (not last_timestamp or timestamp > last_timestamp) and timestamp > file_date:
                    last_timestamp = timestamp
    return {"date": file_date,
            "filepath": file_path,
            "start": first_timestamp,
            "end": last_timestamp,
            "period": last_timestamp - first_timestamp if last_timestamp and first_timestamp else None}


def get_notes_history(end_date=get_fridays_date()):
    # Get list of files from the past week
    week_start_date = end_date - datetime.timedelta(days=6)
    dir_path = os.path.abspath(os.path.join(os.path.expanduser('~'), 'notes'))
    files_list = [fl for fl in os.listdir(dir_path) if is_filename_between_dates(fl, week_start_date, end_date)]
    res = {}
    for x in files_list:
        res[x] = get_file_history(os.path.join(dir_path, x))
    return res


def print_notes_times(fridays_date=get_fridays_date()):
    print('{:<24} End of the week\n\n======= Weeks End Times ========\n'.format(datetime.datetime.now().strftime(DATE_TIME_FORMAT)))
    data = get_notes_history(fridays_date)
    for key in sorted(data.iterkeys()):
        val = data[key]
        end_str = "{end:%H:%M}".format(**val) if val["end"] else "     "
        print('{:%Y-%m-%d}   {:%H:%M}   {}   {}'.format(val["date"], val["start"], end_str, val["period"]))

    print('\n==============================')


def main():
    todays_date_str = datetime.date.today().isoformat()
    yesterdays_date = (datetime.date.today() - datetime.timedelta(1))

    update_input = True
    is_yesterdays_file = False
    expected_filename = get_todays_file_path()

    (update_input, is_yesterdays_file, last_line) = skip_existing_contents(expected_filename,
                                                                           todays_date_str,
                                                                           yesterdays_date)

    if is_yesterdays_file and last_line != "==============================":
        desired_date = yesterdays_date
    else:
        desired_date = datetime.datetime.now()

    if update_input or (is_yesterdays_file and last_line != "==============================\n"):
        if not last_line.endswith(os.linesep):
            print('')
        print('{:<24} Leaving for the day\n\n'.format(desired_date.strftime(DATE_TIME_FORMAT)), end='')
        all_history = get_chrome_history(desired_date)
        all_history.extend(get_utils_actions(desired_date))
        all_history.extend(get_bash_history2(desired_date))
        print('\n=============    Actions HISTORY ================')

        for line in sorted(all_history):
            print(line)

        if desired_date.weekday() == 4:
            print_notes_times(desired_date)
        print('\n==============================')


if __name__ == "__main__":
#     for line in sorted( get_bash_history2(datetime.datetime.now())):
#         print(line)
#     print_notes_times()
    main()
