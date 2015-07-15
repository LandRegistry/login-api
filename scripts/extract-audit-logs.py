# !/usr/bin/env python
# This script extracts auditing information from log files.
# Example use:
# python3 extract-audit-logs.py /var/log/applications/login-api.log


import re
import sys

audit_entry_pattens = list(map(lambda s: re.compile(s), [
    '.*message=\\[User .+ logged in.+',
    '.*message=\\[User .+ logged out.+',
    ".*message=\\[VIEW REGISTER: Title number .+ was viewed by .+",
    ".*message=\\[SEARCH REGISTER: '.*' was searched by '.+'",
    '.*message=\\[Too many bad logins.+',
    '.*message=\\[Invalid credentials used.+',
    '.*message=\\[Created user .+',
    '.*message=\\[Updated user .+',
    '.*message=\\[Deleted user .+',
    '.*message=\\[Reset failed login attempts for user .+',
]))


def _is_audit_line(line):
    for pattern in audit_entry_pattens:
        if pattern.match(line):
            return True

    return False


if len(sys.argv) != 2:
    exit('Should specify the full path to the log file as the only argument')
else:
    with open(sys.argv[1]) as file:
        for line in file:
            if _is_audit_line(line):
                print(line, end='')
