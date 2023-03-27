#!/usr/bin/env python
from __future__ import unicode_literals
from prettify.app import register_reader
from prettify import messages
import datetime

def read_weechat(infile, args):
    for line in infile:
        if len(line.strip()) != 0:
            line_parts = line.strip().split()
            timestamp = datetime.datetime.strptime(" ".join(line_parts[0:2]),
                    "%Y-%m-%d %H:%M:%S")
            if line_parts[2] == "*":
                message = messages.Action(line_parts[3],
                        " ".join(line_parts[4:]))
            elif line_parts[2] in ["--", "irc:"]:
                message = messages.System(" ".join(line_parts[3:]))
            elif line_parts[2] == "-->":
                message = messages.Join(line_parts[3])
            elif line_parts[2] == "<--":
                if line_parts[6] == "quit":
                    message = messages.Quit(line_parts[3])
                else:
                    message = messages.Part(line_parts[3])
            else:  # TODO: find example of notice, account for it
                message = messages.PrivMsg(line_parts[2],
                        " ".join(line_parts[3:]))
            yield (timestamp, message)

register_reader(read_weechat, "weechat", "reads WeeChat logs")
