#!/usr/bin/env python
from __future__ import unicode_literals
from prettify.app import register_renderer
from prettify import messages

def render_plaintext(line_generator, args):
    max_name_length = args.max_name_length

    if args.single_pass:
        lines = line_generator
    else:
        lines = list(line_generator)
        preset_max_name_length = max_name_length
        max_name_length = 0
        for (timestamp, message) in lines:
            if isinstance(message, messages.PrivMsg):
                username_length = len(message.username)
            elif isinstance(message, messages.Notice):
                username_length = len(message.username) + 2
            elif isinstance(message, messages.Action):
                username_length = 1
            elif isinstance(message, messages.System):
                username_length = 2
            elif isinstance(message, messages.Join) or isinstance(message,
                    messages.Part) or isinstance(message, messages.Quit):
                username_length = 3

            if username_length >= preset_max_name_length:
                max_name_length = preset_max_name_length
            elif username_length > max_name_length:
                max_name_length = username_length


    for (timestamp, message) in lines:
        if args.keep_timestamp:
            if args.keep_date:
                gutter = "{0}  ".format(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                gutter = "{0}  ".format(timestamp.strftime("%H:%M:%S"))
        else:
            gutter = ""

        if isinstance(message, messages.PrivMsg):
            gutter += " " * (max_name_length - len(message.username))
            gutter += message.username
        elif isinstance(message, messages.Notice):
            gutter += " " * (max_name_length - (len(message.username) + 2))
            gutter += "-{0}-".format(message.username)
        elif isinstance(message, messages.Action):
            gutter += " " * (max_name_length - 1)
            gutter += "*"
        elif isinstance(message, messages.System):
            gutter += " " * (max_name_length - 2)
            gutter += "--"
        elif isinstance(message, messages.Join):
            gutter += " " * (max_name_length - 3)
            gutter += "-->"
        elif isinstance(message, messages.Part):
            gutter += " " * (max_name_length - 3)
            gutter += "<--"
        elif isinstance(message, messages.Quit):
            gutter += " " * (max_name_length - 3)
            gutter += "-!-"
        gutter += " "

        if isinstance(message, messages.PrivMsg) or isinstance(message,
                messages.Notice) or isinstance(message, messages.System):
            text = message.text
        elif isinstance(message, messages.Action):
            text = "{0} {1}".format(message.username, message.text)
        elif isinstance(message, messages.Join):
            text = "{0} joined".format(message.username)
        elif isinstance(message, messages.Part):
            text = "{0} left".format(message.username)
        elif isinstance(message, messages.Quit):
            text = "{0} quit".format(message.username)
        text_parts = text.split(" ")

        pretty_lines = [gutter]
        while text_parts != []:
            if len(text_parts[0]) + len(pretty_lines[-1]) + 1 > args.page_width:
                if len(text_parts[0]) + len(gutter) + args.indent_depth + 1 > args.page_width:
                    pretty_lines[-1] += " {0}".format(text_parts.pop(0))
                    if text_parts != []:
                        pretty_lines.append(" " * (len(gutter) + args.indent_depth))
                else:
                    pretty_lines.append(" " * (len(gutter) + args.indent_depth))
                    pretty_lines[-1] += " {0}".format(text_parts.pop(0))
            else:
                pretty_lines[-1] += " {0}".format(text_parts.pop(0))

        for line in pretty_lines: yield "{0}\n".format(line)

register_renderer(render_plaintext, "plaintext", "emits reflowed plaintext",
        (('-1', '--single-pass', {
            'action': 'store_true',
            'dest': 'single_pass',
            'help': '''Skip
                the name-length-check pass. All names will be indented to the preset
                maximum name length. Required if operating in a pipeline.''',
            }),
         ('-m', '--max-name-length', {
             'action': 'store',
             'type': int,
             'default': 24,
             'dest': 'max_name_length',
             'help': '''Maximum name length - in single-pass mode, all
                names will be indented to this length. In two-pass mode, the
                name-length-check pass will terminate prematurely if this length is
                met or exceeded, allowing the first pass time to be shortened in
                some cases.''',
             }),
         ('-w', '--output-width', {
             'action': 'store',
             'type': int,
             'default': 80,
             'dest': 'page_width',
             'help': '''Width to reflow the log to.''',
             }),
         ('-dd', '--drop-date', {
            'action': 'store_false',
            'dest': 'keep_date',
            'help': '''Drop the date portion of the timestamp. This is implied
                by --drop-timestamp, so only the latter is needed if both
                effects are desired.''',
            }),
         ('-dt', '--drop-timestamp', {
            'action': 'store_false',
            'dest': 'keep_timestamp',
            'help': '''Drop the timestamp, leaving just the log text. Implies
                --drop-date.''',
            }),
         ('-id', '--indent', {
             'action': 'store',
             'type': int,
             'default': 0,
             'dest': 'indent_depth',
             'help': '''Depth to indent continuation lines to.''',
             }),
        ))
