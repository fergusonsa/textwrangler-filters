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
        return file.readlines()
    else:
        return None

def get_chrome_history(for_date=datetime.date.today()):

    history_file_path = find_path()
    allrows = None
    date_str = for_date.strftime('%Y-%m-%d')
    try:
        con = sqlite3.connect(find_path()) #Connect to the database
        con.text_factory = str
        c = con.cursor()

        rows = c.execute('select datetime(last_visit_time/1000000-11644473600,"unixepoch"),title, url from urls where datetime(last_visit_time/1000000-11644473600,"unixepoch") >= datetime("' + date_str + 'T00:00") order by last_visit_time desc')
        allrows = rows.fetchall()
        con.close()
    finally:
        cleanup(history_file_path)
    return allrows

def run_command(cmd):
    """given shell command, returns communication tuple of stdout and stderr
    based on https://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output"""
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE).communicate()

def run_command2(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         shell=True, executable="/bin/bash")
    # Read stdout from subprocess until the buffer is empty !
    for line in iter(p.stdout.readline, b''):
        if line: # Don't print blank lines
            yield line
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:
        sleep(.1) #Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    if p.returncode != 0:
       # The run_command() function is responsible for logging STDERR
       print("Error: '" + str(err) + "'")

def run_command3(exe):
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True)
    (stdout, stderr) = p.communicate()
                         ## Wait for date to terminate. Get return returncode ##
    p_status = p.wait()
    print( "Command output : ", stdout)
    print( "Command exit status/return code : ", p_status)
    for line in stdout:
        if line and pattern.match(line): # Don't print blank lines
            yield line



def get_bash_history(for_date=datetime.date.today()):
    date_str = for_date.strftime('%Y-%m-%d')
    pattern = re.compile("^ *[0-9]*  {}.*".format(date_str))
    cmd = 'bash -i -c "history -r; history"'
#     cmd = 'bash -i -c "history"'
#     cmd = 'history'
    print('date_str: "{}" command: "{}"'.format(date_str, cmd))
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    # Read stdout from subprocess until the buffer is empty !
    for line in iter(p.stdout.readline, b''):
        if line and pattern.match(line): # Don't print blank lines
            yield line
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:
        sleep(.1) #Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    if p.returncode != 0:
       # The run_command() function is responsible for logging STDERR
       print("Error: '" + str(err) + "'")


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

    if update_input or (is_yesterdays_file and last_line != "=============================="):
        if not last_line.endswith(os.linesep):
            print('')
        print('{:<24} Leaving for the day\n\n'.format(desired_date.strftime(DATE_TIME_FORMAT)), end='')
        print('\nToday''s Chrome history:\n==============================\n')
        for row in get_chrome_history(desired_date):
            print('{0[0]}  {0[1]:70}  {0[2]}'.format(row))
        print('\n==============================\n\n')
        print('\nToday''s bash history:\n==============================\n')
        for line in get_bash_history(desired_date):
            print(line, end='')
        print('\n==============================\n\n')
        print('\nToday''s clojure utils action history:\n==============================\n')
        print(get_utils_actions(desired_date))
        print('\n==============================')


