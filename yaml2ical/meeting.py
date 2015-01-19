# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
import hashlib
import os
import yaml


class Schedule(object):
    """A meeting schedule."""

    def __init__(self, meeting, sched_yaml):
        """Initialize schedule from yaml."""

        self.project = meeting.project
        self.filename = meeting.filename
        self.time = datetime.datetime.strptime(sched_yaml['time'], '%H%M')
        self.day = sched_yaml['day']
        self.irc = sched_yaml['irc']
        self.freq = sched_yaml['frequency']

    def __eq__(self, other):
        #TODO(ttx): This is a bit overzealous (it will report as conflict
        # biweekly-odd/biweekly-even on same date/hour/irc) so this should be
        # revamped especially if we want to add more complex recurrence rules
        return ((self.day == other.day) and
                (self.time == other.time) and
                (self.irc == other.irc))


class Meeting(object):
    """An OpenStack meeting."""

    def __init__(self, meeting_yaml):
        """Initialize meeting from meeting yaml description."""

        yaml_obj = yaml.safe_load(meeting_yaml)
        self.chair = yaml_obj['chair']
        self.description = yaml_obj['description']
        self.project = yaml_obj['project']
        self.filename = "%s-%s" % (
            yaml_obj['project'],
            hashlib.md5(str(yaml_obj).encode('utf-8')).hexdigest()[:8])

        self.schedules = []
        for sch in yaml_obj['schedule']:
            s = Schedule(self, sch)
            self.schedules.append(s)


def load_meetings(yaml_source):
    """Build YAML object and load meeting data

    :param yaml_source: source data to load, which can be a directory or
                        stream.
    :returns: list of meeting objects
    """
    meetings_yaml = []
    # Determine what the yaml_source is
    if os.path.isdir(yaml_source):
        # TODO(lbragstad): use os.path.walk?
        for f in os.listdir(yaml_source):
            # Build the entire file path and append to the list of yaml
            # meetings
            yaml_file = os.path.join(yaml_source, f)
            meetings_yaml.append(yaml_file)
    elif isinstance(yaml_source, str):
        return [Meeting(yaml_source)]
    else:
        # If we don't have a .yaml file, a directory of .yaml files, or any
        # YAML data fail out here.
        raise ValueError("YAML source isn't a .yaml file, directory "
                         "containing .yaml files, or YAML data.")

    meetings = []
    for yaml_file in meetings_yaml:
        with open(yaml_file, 'r') as f:
            meetings.append(Meeting(f))

    return meetings


class MeetingConflictError(Exception):
    pass


def check_for_meeting_conflicts(meetings):
    """Check if a list of meetings have conflicts.

    :param meetings: list of Meeting objects

    """

    for i in range(len(meetings)):
        schedules = meetings[i].schedules
        for j in range(i + 1, len(meetings)):
            other_schedules = meetings[j].schedules
            for schedule in schedules:
                for other_schedule in other_schedules:
                    if schedule == other_schedule:
                        msg_dict = {'one': schedule.filename,
                                    'two': other_schedule.filename}
                        raise MeetingConflictError(
                            "Conflict between %(one)s and %(two)s." % msg_dict)