#!/usr/bin/python
from __future__ import print_function
import datetime
import fileinput
import numbers
import os
import os.path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import refreshbooks.api
import yaml
import webbrowser

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

END_OF_WEEK_DAY = 4

def get_config():
    cfg_file_path = os.path.join( os.environ.get("HOME"), ".tracker", "config.cfg")

def find_path():
    file_path = os.path.join( os.environ.get("HOME"), 'Library', 'Application Support', 'Google', 'Chrome', 'Profile 1', 'History')
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(file_path, temp_path)
    return temp_path


def cleanup(file_path):
    shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)


def get_utils_actions(for_date=None):
    """
    Check for utils action log file for desired date.
    If present, return its contents
    """
    if for_date is None:
        for_date=datetime.date.today()
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


def get_chrome_history(for_date=None):
    if for_date is None:
        for_date=datetime.date.today()

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


def get_bash_history2(for_date=None):
    if for_date is None:
        for_date=datetime.date.today()
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


def get_todays_file_path(todays_date_str=None):
    if todays_date_str is None:
        todays_date_str=datetime.date.today().isoformat()
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


def get_end_of_week_date(todays_date=None):
    if todays_date is None:
        todays_date=datetime.date.today()
    target_dayofweek = 4  # Friday
    current_dayofweek = todays_date.weekday() # Today

    if END_OF_WEEK_DAY <= current_dayofweek:
        # target is in the current week
        return todays_date - datetime.timedelta(days=(current_dayofweek - END_OF_WEEK_DAY))

    else:
        # target is in the previous week
        return todays_date - datetime.timedelta(weeks=1) + datetime.timedelta(days=(END_OF_WEEK_DAY - current_dayofweek))


def is_filename_between_dates(file_path, start_date, end_date):
    if not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    if not isinstance(end_date, datetime.datetime):
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
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

    if file_date.date() == datetime.date.today() and (last_timestamp is None or datetime.datetime.now() > last_timestamp):
        last_timestamp = datetime.datetime.now()

    return {"date": file_date,
            "filepath": file_path,
            "start": first_timestamp,
            "end": last_timestamp,
            "period": last_timestamp - first_timestamp if last_timestamp and first_timestamp else None}


def get_notes_history(end_date=None):
    if end_date is None:
        end_date=get_end_of_week_date()
    # Get list of files from the past week
    week_start_date = end_date - datetime.timedelta(days=6)
    dir_path = os.path.abspath(os.path.join(os.path.expanduser('~'), 'notes'))
    files_list = [fl for fl in os.listdir(dir_path) if is_filename_between_dates(fl, week_start_date, end_date)]
    res = {}
    for x in files_list:
        res[x] = get_file_history(os.path.join(dir_path, x))
    return res


def print_notes_times(end_of_week_date=None, hours_data=None):
    if end_of_week_date is None:
        end_of_week_date=get_end_of_week_date()
    if hours_data is None:
        hours_data = get_notes_history(end_of_week_date)
    print('{:<24} End of the week\n\n======= Weeks End Times ========\n'.format(datetime.datetime.now().strftime(DATE_TIME_FORMAT)))
    total_hours = datetime.timedelta()
    for key in sorted(hours_data.iterkeys()):
        val = hours_data[key]
        total_hours += val["period"]
        end_str = "{end:%H:%M}".format(**val) if val["end"] else "     "
        print('{:%Y-%m-%d}   {:%H:%M}   {}   {}'.format(val["date"], val["start"], end_str, val["period"]))
    print("Total Hours: {}".format(total_hours))

def get_timesheet_config():
    file_path = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                            '.ssh', 'identity.yaml'))
    stream = file(file_path, 'r')
    config = yaml.load(stream)
    return config

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

def update_freshbooks_timesheet(end_of_week_date=None, hours_data=None, config=None):
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()
    if hours_data is None:
        hours_data = get_notes_history(end_of_week_date)
    if config is None:
        config = get_timesheet_config()

    print(config)
#     example source http://pydoc.net/clifresh/5/clifresh/
    c = refreshbooks.api.TokenClient(config['freshbooks']['api']['url'],
                                     config['freshbooks']['api']['secret'],
                                     user_agent=config['freshbooks']['api']['user-agent'])
    project_name = config['current-project']

    p = c.project.list()
    pr = p.projects.project
    task_list = c.task.list(project_id=pr.project_id)
#     task_list.tasks.task.task_id
#     tes = c.time_entry.list(project_id=pr.project_id, date_from='2017-11-18', date_to='2017-11-24')
#     for te in tes.time_entries.time_entry:
#         print(te.date, te.hours, te.billed)
    daily_hours = config[project_name]['daily-hours']
    if isinstance(daily_hours, numbers.Number):
        for day in hours_data.itervalues():
            t_resp = c.time_entry.create(time_entry={"date": day['date'].isoformat(),
                                                     "project_id": pr.project_id,
                                                     "task_id": task_list.tasks.task.task_id,
                                                     "hours": daily_hours})
    else:
        print('Cannot handle non-numeric project daily-hours config setting yet!')

def prep_timesheets_invoice(hours, end_of_week_date=None, config=None):
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()
    if config is None:
        config = get_timesheet_config()
    project = config['current-project']
    for ts in config[project]['timesheets']:
        webbrowser.open(ts['url'])
    webbrowser.open(config['freshbooks']['login-url'])
    new_filename = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                                'notes',
                                                'Flex Contractor - Weekly Project Tracking Sheet {} Scott Ferguson.docx'.format(
                                                    end_of_week_date.isoformat())))
    previous_filename = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                                     'notes',
                                                     'Flex Contractor - Weekly Project Tracking Sheet {} Scott Ferguson.docx'.format(
                                                         (end_of_week_date - datetime.timedelta(weeks=1)).isoformat())))
    if not os.path.exists(new_filename):
        shutil.copy2(previous_filename, new_filename)
    os.system("open {}".format(new_filename))


def days_end_main():
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
    days_end_main()
