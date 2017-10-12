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
BASH_HISTORY_INPUT_PATTERN = re.compile("^([^ ]*)\s*([0-9]*)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)$")
BASH_INPUT_PATTERN = re.compile("^\s*([0-9]*)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)$")
UTILS_ACTION_INPUT_PATTERN = re.compile("^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)(\n?)$")

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


def reformat_bash_history(line):
    """
    Parse the incoming line of bash history into a "standard" format

    Expected incoming format for each line:
      158  2017-10-02 17:58:14 	orca stop

    Expected output format for each line:
    2017-10-02 17:58:14  bash  158  orca stop
    """
    matches = BASH_INPUT_PATTERN.match(line)
    if len(matches.groups()) > 0:
        return OUTPUT_FORMAT.format(matches.group(2), "bash", matches.group(1) + "  " + matches.group(3))
    else:
        return ""


def get_bash_history2(for_date=datetime.date.today()):
    res_lines = []
    date_str = for_date.strftime('%Y-%m-%d')
    path = os.path.join(os.environ.get("HOME"), "reports", "bash_history", "bash_history-{}.txt".format(date_str))
    if os.path.isfile(path):
        file = open(path, 'r')
        for line in file.readlines():
            matches = BASH_HISTORY_INPUT_PATTERN.match(line)
            res_lines.append(OUTPUT_FORMAT.format(matches.group(3), "bash", matches.group(1) + " " + matches.group(2) + " " + matches.group(4)))

    return list(set(res_lines))

def get_bash_history(for_date=datetime.date.today()):
    res_lines = []
    date_str = for_date.strftime('%Y-%m-%d')
    pattern = re.compile("^ *[0-9]*  {}.*".format(date_str))
#     cmd = 'bash -i -c "history -r; history"'
    cmd = 'bash -i -c "history -n; history"'
#     cmd = 'bash -i -c "history"'
#     cmd = 'history'
#     print('date_str: "{}" command: "{}"'.format(date_str, cmd))
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    # Read stdout from subprocess until the buffer is empty !
    for line in iter(p.stdout.readline, b''):
        if line and pattern.match(line): # Don't print blank lines
            res_lines.append(reformat_bash_history(line))
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:
        sleep(.1) #Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    if p.returncode != 0:
       # The run_command() function is responsible for logging STDERR
       print("Error: '" + str(err) + "'")
    return res_lines

if __name__ == "__main__":
    todays_date_str = datetime.date.today().isoformat()
    yesterdays_date = (datetime.date.today() - datetime.timedelta(1))

    update_input = True
    is_yesterdays_file = False
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
            is_yesterdays_file = line.startswith(yesterdays_date.isoformat())

        print(line, end='')

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
        print('\n==============================')
