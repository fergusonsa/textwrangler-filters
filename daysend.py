#!/usr/bin/python
from __future__ import print_function
import datetime
import fileinput
import httplib2
import lxml.objectify
import numbers
import os
import os.path
import re
import refreshbooks.api
import shutil
import sqlite3
import string
import subprocess
import sys
import tempfile
import traceback
import webbrowser
import yaml
import glob 

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

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

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = '/Users/fergusonsa/.credentials/client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S-%HH:%MM'


class DeltaTemplate(string.Template):
    delimiter = "%"


def timedelta_format(tdelta, fmt):
    """ adapted from https://stackoverflow.com/questions/8906926/formatting-python-timedelta-objects

    """
    data = {'D': tdelta.days}
    data['H'], rem = divmod(tdelta.seconds, 3600)
    data['M'], data['S'] = divmod(rem, 60)

    if '%D'not in fmt:
        data['H'] += 24 * data['D']
    if '%H'not in fmt:
        data['M'] += 60 * data['H']
    if '%M'not in fmt:
        data['S'] += 60 * data['M']

    t = DeltaTemplate(fmt)
    return t.substitute(**data)


def parse_isoformat_datetime(dt_str):
#     conformed_timestamp = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', dt_str)
#     return datetime.datetime.strptime(conformed_timestamp, "%Y%m%dT%H%M%S.%f" )
    # this regex removes all colons and all
    # dashes EXCEPT for the dash indicating + or - utc offset for the timezone
    conformed_timestamp = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', dt_str)

    # split on the offset to remove it. use a capture group to keep the delimiter
    split_timestamp = re.split(r"[+|-]",conformed_timestamp)
    main_timestamp = split_timestamp[0]
    if len(split_timestamp) == 3:
        sign = split_timestamp[1]
        offset = split_timestamp[2]
    else:
        sign = None
        offset = None

    # generate the datetime object without the offset at UTC time
    output_datetime = datetime.datetime.strptime(main_timestamp +"Z", "%Y%m%dT%H%M%SZ" )
    if offset:
        # create timedelta based on offset
        offset_delta = datetime.timedelta(hours=int(sign+offset[:-2]), minutes=int(sign+offset[-2:]))
        # offset datetime with timedelta
        output_datetime = output_datetime + offset_delta
    return output_datetime


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials =  store.get()
    if not credentials or credentials.invalid:
        print('did not get credentials via {}'.format(credential_path))
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_google_calendar_events_for_day(creds=None, http=None, service=None, dt=None):
    if not creds:
        creds = get_credentials()
    if not http:
        http = credentials.authorize(httplib2.Http())
    if not service:
        service = discovery.build('calendar', 'v3', http=http)
    if not dt:
        dt = datetime.datetime.today()

    st_of_day = datetime.datetime.combine(dt.date(), datetime.time())
    end_of_day = st_of_day + datetime.timedelta(days=1)

    eventsResult = service.events().list(
        calendarId='primary', timeMin=st_of_day.isoformat() + 'Z', timeMax=end_of_day.isoformat() + 'Z', singleEvents=True,
        orderBy='startTime').execute()
    return eventsResult.get('items', [])


def print_google_calendar_events(events, output=sys.stdout):
    if not events:
        output.write('No upcoming events found.\n')
    else:
        for event in events:
            start = parse_isoformat_datetime(event['start'].get('dateTime', event['start'].get('date')))
            end = event['end'].get('dateTime', event['end'].get('date'))
            length = parse_isoformat_datetime(end) - start
            output.write('{:<24} {} {} {}\n'.format(start.strftime(daysend.DATE_TIME_FORMAT),
                                                    event['summary'],
                                                    timedelta_format(length, '%H hours %M minutes'),
                                                    event['location']))


def get_config():
    """ IN PROGRESS """
    cfg_file_path = os.path.join( os.environ.get('HOME'), ".tracker", "config.cfg")


def get_chrome_history_copy_path():
    """ Creates a copy of the history file for the first profile of Google Chrome in a newly
    created temporary directory and returns the path. Note that it will not find any other
    profile.
    """
    file_path = os.path.join(os.environ.get('HOME'), 'Library', 'Application Support',
                             'Google', 'Chrome', 'Profile 1', 'History')
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(file_path, temp_path)
    return temp_path


def get_chrome_history_copy_paths(for_date=None):
    """ Creates a copy of the history file for the first profile of Google Chrome in a newly
    created temporary directory and returns the path. Note that it will not find any other
    profile.
    """
    if not for_date:
        for_date = datetime.date.today()
    paths = []
    user_path = os.path.join(os.environ.get('HOME'), 'Library', 'Application Support',
                             'Google', 'Chrome')
    temp_dir = tempfile.mkdtemp()
    for_date_midnight_timestamp = datetime.datetime.combine(for_date, datetime.datetime.min.time())
    for file in glob.glob(user_path + '/*/History'):
        mod_file_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file))
        if mod_file_timestamp > for_date_midnight_timestamp:
            profile_name = os.path.basename(os.path.dirname(file))
            temp_path = os.path.join(temp_dir, profile_name + '_History')
            shutil.copy2(file, temp_path)
            paths.append(temp_path)
    return paths


def cleanup(dir_path):
    if os.path.isfile(dir_path):    
        dir_path = os.path.dirname(dir_path)
    if os.path.exists(dir_path) and dir_path != os.path.expanduser('~') and dir_path != '/':
#         print('Deleting files in {}'.format(dir_path))
        shutil.rmtree(dir_path)
#         shutil.rmtree(dir_path, ignore_errors=True)
#     else:
#         print('NOT DELETING FILES IN {}'.format(dir_path))


def get_utils_actions(for_date=None):
    """
    Check for utils action log file for desired date.
    If present, return its contents
    """
    if for_date is None:
        for_date=datetime.date.today()
    date_str = for_date.strftime('%Y%m%d')
    path = os.path.join(os.environ.get('HOME'), 'reports', 'action-logs',
                        'action-log-{}.txt'.format(date_str))
    res_lines = []
    if os.path.isfile(path):
        file = open(path, 'r')
        for line in file.readlines():
            matches = UTILS_ACTION_INPUT_PATTERN.match(line)
            res_lines.append(OUTPUT_FORMAT.format(matches.group(1), 'Utils Action', matches.group(2)))
    return res_lines


def get_chrome_history(for_date=None):
    if for_date is None:
        for_date=datetime.date.today()

    history_file_paths = get_chrome_history_copy_paths(for_date)
#     print(history_file_paths)
    allrows = []
    res_lines = []
    date_str = for_date.isoformat()
    next_date_str = (for_date + datetime.timedelta(days=1)).isoformat()
#     print('date_str: {}   next_date_str: {}'.format(date_str, next_date_str))
    for history_file_path in history_file_paths:
        try:
            con = sqlite3.connect(history_file_path) #Connect to the database
            con.text_factory = str
            c = con.cursor()
            rows = c.execute("""select datetime(last_visit_time/1000000-11644473600,
                                "unixepoch", "localtime"),title, url 
                                from urls 
                                where datetime(last_visit_time/1000000-11644473600,"unixepoch", "localtime") >= datetime("{}T00:00")
                                and datetime(last_visit_time/1000000-11644473600,"unixepoch", "localtime") < datetime("{}T00:00")
                                order by last_visit_time desc""".format(date_str, next_date_str))
            allrows = rows.fetchall()
#             print(len(allrows))
            con.close()
            for line in allrows:
                res_lines.append(OUTPUT_FORMAT.format(line[0], 'Chrome', line[1] + ' ' + line[2]))
        except:
            e = sys.exc_info()
            print('\nEXCEPTION trying to get google history from {}! {} \n{} \n{}'.format(history_file_path, e[0], e[1], e[2]))

    if len(history_file_paths) > 0:
        cleanup(history_file_paths[0])
    return res_lines


def get_bash_history2(for_date=None):
    if for_date is None:
        for_date=datetime.date.today()
    res_lines = []
    date_str = for_date.strftime('%Y-%m-%d')
    path = os.path.join(os.environ.get('HOME'), 
                        "reports", 
                        "bash_history", 
                        "bash_history-{}.txt".format(date_str))
    if os.path.isfile(path):
        file = open(path, 'r')
        for line in file.readlines():
            matches = BASH_HISTORY_INPUT_PATTERN.match(line)
            if matches:
                res_lines.append(OUTPUT_FORMAT.format(matches.group(4), 
                                                      'bash', 
                                                      matches.group(1) + ' ' + matches.group(2) + ' ' + matches.group(5)))
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
            parts = NOTE_FILE_LINE_PATTERN.match(line)
            if parts:
                start_timestamp = datetime.datetime(int(parts.group(1)), int(parts.group(2)), int(parts.group(3)),
                                              int(parts.group(4)), int(parts.group(5)))
            else:
                start_timestamp = None
            is_yesterdays_file = line.startswith(previous_date.isoformat())

        print(line, end='')
    return update_input, is_yesterdays_file, last_line, start_timestamp


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

    return {"date": file_date.date(),
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
        print('{:%Y-%m-%d}   {:%H:%M}   {}   {}'.format(val["date"], val["start"], end_str, 
                                                        timedelta_format(val["period"], '%H hours %M minutes')))
    print("Total Hours: {}".format(timedelta_format(total_hours, '%H hours %M minutes')))


def get_timesheet_config():
    """
    """
    file_path = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                            '.ssh', 'identity.yaml'))
    stream = file(file_path, 'r')
    config = yaml.load(stream)
    return config


def create_freshbooks_client(config=None):
    if config is None:
        config = get_timesheet_config()
    return refreshbooks.api.TokenClient(config['freshbooks']['api']['url'],
                                        config['freshbooks']['api']['secret'],
                                        user_agent=config['freshbooks']['api']['user-agent'])


"""
from daysend import *
end_of_week_date = get_end_of_week_date()
hours = get_notes_history()
config = get_timesheet_config()
c = create_freshbooks_client(config)

update_freshbooks_timesheet(end_of_week_date, hours)
create_invoice(end_of_week_date, config)
prep_timesheets(hours, end_of_week_date)

"""
def update_freshbooks_timesheet(end_of_week_date=None, hours_data=None, config=None):
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()
    if hours_data is None:
        hours_data = get_notes_history(end_of_week_date)
    if config is None:
        config = get_timesheet_config()

#     example source http://pydoc.net/clifresh/5/clifresh/
    c = create_freshbooks_client(config)
    project_name = config['current-project']
    project_id = config[project_name]['freshbooks']['project-id']
    task_id = config[project_name]['freshbooks']['task-id']
    hours_per_day = config[project_name]['daily-hours']
    task_list = c.task.list(project_id=project_id)

    week_start_date = end_of_week_date - datetime.timedelta(days=6)
    tes = c.time_entry.list(project_id=project_id, date_from=week_start_date.isoformat(), date_to=end_of_week_date.isoformat())
    if tes.time_entries.get('total') != '0':
        print('Existing time entries between {} and {}'.format(week_start_date.isoformat(), end_of_week_date.isoformat()))
        for te in tes.time_entries.time_entry:
            print(te.date, te.hours, te.billed)
    if isinstance(hours_per_day, numbers.Number):
        for day in hours_data.itervalues():
            if tes.time_entries.get('total') != '0':
                tentry = [te for te in tes.time_entries.time_entry if te.date == day['date'].date().isoformat()]
            else:
                tentry = None
            if not tentry:
                print('Creating time entry for {} project id: {} task id: {} hours: {}'.format(day['date'].isoformat(), project_id, task_id, hours_per_day))
                t_resp = c.time_entry.create(time_entry={'date': day['date'].isoformat(),
                                                         'project_id': project_id,
                                                         'task_id': task_id,
                                                         'hours': hours_per_day})
            else:
                print('Already a time entry of {} hours for {}'.format(tentry[0].hours, tentry[0].date))
    else:
        print('Cannot handle non-numeric project daily-hours config setting yet!')


def prep_timesheets(hours, end_of_week_date=None, config=None):
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()
    if config is None:
        config = get_timesheet_config()
    project = config['current-project']
    for ts in config[project]['timesheets']:
        webbrowser.open(ts['url'])
    webbrowser.open(config['freshbooks']['login-url'])
    new_filename = os.path.abspath(os.path.join(os.environ.get('HOME'),
                                                'notes',
                                                'Flex Contractor - Weekly Project Tracking Sheet {} Scott Ferguson.docx'.format(
                                                    end_of_week_date.isoformat())))
    previous_filename = os.path.abspath(os.path.join(os.environ.get('HOME'),
                                                     'notes',
                                                     'Flex Contractor - Weekly Project Tracking Sheet {} Scott Ferguson.docx'.format(
                                                         (end_of_week_date - datetime.timedelta(weeks=1)).isoformat())))
    if not os.path.exists(previous_filename):
        print('The file "{}" does not exist as expected!'.format(previous_filename, new_filename))
    else:
        if not os.path.exists(new_filename):
            print('Copying "{}" to "{}"'.format(previous_filename, new_filename))
            shutil.copy2(previous_filename, new_filename)
        else:
            print('The new file "{}" already exists!'.format(new_filename))
        os.system('open "{}"'.format(new_filename))


def get_month_first_date(dtDateTime):
    """From http://code.activestate.com/recipes/476197-first-last-day-of-the-month/ """
    #what is the first day of the current month
    ddays = int(dtDateTime.strftime("%d"))-1 #days to subtract to get to the 1st
    delta = datetime.timedelta(days= ddays)  #create a delta datetime object
    return dtDateTime - delta


def get_month_last_date(dtDateTime):
    """From http://code.activestate.com/recipes/476197-first-last-day-of-the-month/ """
    dYear = dtDateTime.strftime("%Y")        #get the year
    dMonth = str(int(dtDateTime.strftime("%m"))%12+1)#get next month, watch rollover
    dDay = "1"                               #first day of next month
    nextMonth = mkDateTime("%s-%s-%s"%(dYear,dMonth,dDay))#make a datetime obj for 1st of next month
    delta = datetime.timedelta(seconds=1)    #create a delta of 1 second
    return nextMonth - delta                 #subtract from nextMonth and return


def create_invoice(end_of_week_date=None, config=None):
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()
    if config is None:
        config = get_timesheet_config()

    project_name = config['current-project']
    if config[project_name]['invoice-frequency'] == 'weekly':
        end_date = get_end_of_week_date()
        start_date = end_date - datetime.timedelta(days=6)
    elif config[project_name]['invoice-frequency'] == 'monthly':
        end_date = get_month_last_date(get_end_of_week_date())
        start_date = get_month_first_date(end_date)

    c = create_freshbooks_client(config)

    project_id = config[project_name]['freshbooks']['project-id']
    client_id = config[project_name]['freshbooks']['client-id']
    # Get the task details to help fill out the lines of the invoice
    default_tsk = c.task.get(task_id=config[project_name]['freshbooks']['task-id'])
    # Get the list of time entries to add to the invoice
    tes = c.time_entry.list(project_id=project_id,
                            date_from=start_date.isoformat(),
                            date_to=end_date.isoformat())
    if tes.time_entries.get('total') != '0':
        # Check the number of unbilled hours to be added to the invoice
        print("list of hours: ", [float(te.hours.text) for te in tes.time_entries.time_entry if te.billed.text == '0'])
        num_hours = sum([float(te.hours.text) for te in tes.time_entries.time_entry if te.billed.text == '0'])
        print("num_hours: {}".format(num_hours))
        if num_hours > 0:
#             if num_hours !=
            # Create the invoice to add lines to.
            response = c.invoice.create(invoice=dict(client_id=client_id))
            invoice_response = c.invoice.get(invoice_id=response.invoice_id)

            print("New invoice created: #{} (id {})".format(invoice_response.invoice.number,
                                                            invoice_response.invoice.invoice_id))
            tasks_details = {config[project_name]['freshbooks']['task-id']: default_tsk}
            for te in tes.time_entries.time_entry:
                if te.billed.text == '0':
                    tsk = tasks_details[te.task_id]
                    added = c.invoice.lines.add(invoice_id=invoice_response.invoice.invoice_id,
                                                lines=[refreshbooks.api.types.line(name=tsk.task.name,
                                                                                   unit_cost=tsk.task.rate,
                                                                                   quantity=te.hours,
                                                                                   amount=(tsk.task.rate * hours),
                                                                                   tax1_name='HST',
                                                                                   tax1_percent=13)])
                    # Mark the time entry as billed
        else:
            print('No unbilled time entries to add to an invoice between the dates {} and {}'.format(start_date.isoformat(), end_date.isoformat()))
            for te in tes.time_entries.time_entry:
                print(te.date, te.hours, te.billed, float(te.hours.text))

    else:
        print('No time entries to add to an invoice between the dates {} and {}'.format(start_date.isoformat(), end_date.isoformat()))
"""
          <amount>40</amount>
          <name>Yard work</name>

          <unit_cost>10</unit_cost>
          <quantity>4</quantity>
          <tax1_name>GST</tax1_name>
          <tax2_name>PST</tax2_name>
          <tax1_percent>5</tax1_percent>
          <tax2_percent>8</tax2_percent>
          <type>Item</type>
"""


def timestamp_main():
    todays_date_str = datetime.date.today().isoformat()
    update_input = True
    expected_filename = get_todays_file_path()

    if not os.path.exists(expected_filename):
        with open(expected_filename, mode='w') as newfile:
            newfile.write('{:<24}Arrived and logged in\n'.format(datetime.datetime.now().strftime(DATE_TIME_FORMAT)))
            try:
                events = get_google_calendar_events_for_day()
                print_google_calendar_events(events, newfile)
            except:
                pass
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
        print('{:<24}'.format(datetime.datetime.now().strftime(DATE_TIME_FORMAT)), end='')


def weeks_end_main(end_of_week_date=None):
    """ IN PROGRESS"""
    if end_of_week_date is None:
        end_of_week_date = get_end_of_week_date()

    hours = get_notes_history()
    config = get_timesheet_config()

    print_notes_times(desired_date, hours)
    update_freshbooks_timesheet(end_of_week_date, hours)
    create_invoice(end_of_week_date, config)
    prep_timesheets(hours, end_of_week_date)


def days_end_main():
    todays_date_str = datetime.date.today().isoformat()
    yesterdays_date = (datetime.date.today() - datetime.timedelta(1))

    update_input = True
    is_yesterdays_file = False
    expected_filename = get_todays_file_path()

    (update_input, is_yesterdays_file, last_line, start_timestamp) = skip_existing_contents(expected_filename,
                                                                           todays_date_str,
                                                                           yesterdays_date)

    if is_yesterdays_file and last_line != "==============================":
        desired_date = yesterdays_date
    else:
        desired_date = datetime.datetime.now()

    if update_input or (is_yesterdays_file and last_line != "==============================\n"):
        if not last_line.endswith(os.linesep):
            print('')
        print('{:<24}Leaving for the day, Hours for today: {}\n'.format(desired_date.strftime(DATE_TIME_FORMAT), datetime.datetime.now() - start_timestamp))

        all_history = get_chrome_history(desired_date.date())
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
