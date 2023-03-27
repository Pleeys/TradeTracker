#!/usr/bin/env python
from __future__ import unicode_literals
from prettify.app import register_renderer
from prettify import messages

# TODO: Style by line type.
template_header = """<!doctype html>
<html lang="en">
<head>
    <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
    <title>{log_name}</title>
    <style type="text/css">
        * {
            box-sizing: border-box;
        }
        body {
            padding: 2.5em;
        }
        h1 {
            margin-top: 0;
            font-size: 1.5em;
            text-align: center;
        }
        h1, .log {
            width: 100%;
        }
        .username {
            font-weight: bold;
        }
        .log {
            border-collapse: collapse;
        }
        .line {
            background-color: lightgray;
            opacity: 1;
            -webkit-transition: opacity .3s ease-in;
            -moz-transition: opacity .3s ease-in;
            -o-transition: opacity .3s ease-in;
            transition: opacity .3s ease-in;
        }
        .line.timeHidden {
            opacity: 0;
        }
        .line td {
            padding: 0.6em;
        }
        .line:nth-child(even) {
            background-color: silver;
        }
        .timerLinks {
            position: fixed;
            top: 0.3em;
            left: 0.3em;
            background-color: #fff;
        }
        .timerLinks a {
            border: none;
            opacity: 0.4;
            -webkit-transition: opacity .3s ease-in;
            -moz-transition: opacity .3s ease-in;
            -o-transition: opacity .3s ease-in;
            transition: opacity .3s ease-in;
            margin: 0.2em;
        }
        .timerLinks a.active {
            opacity: 1;
        }
    </style>
</head>
<body>
    <h1>{log_name}</h1>
    <table class="log">
"""

template_line = {
    "gutter": """        <tr class="line {msg_type}">
            <td class="gutter">{gutter}</td>
            <td class="text">{text}</td>
        </tr>
""",
    "no_gutter": """        <tr class="line {msg_type}">
            <td class="text" colspan=2>{text}</td>
        </tr>
"""}

template_line_timestamp = {
    "gutter": """        <tr class="line {msg_type}">
            <td class="timestamp">{timestamp}</td>
            <td class="gutter">{gutter}</td>
            <td class="text">{text}</td>
        </tr>
""",
    "no_gutter": """        <tr class="line {msg_type}">
            <td class="timestamp">{timestamp}</td>
            <td class="text" colspan=2>{text}</td>
        </tr>
"""}


template_footer = """    </table>
{script}
</body>
</html>
"""

template_script = """<script type="text/javascript">
        var timerLinks = document.createElement("div");
        var timedLink = document.createElement("a");
        var untimedLink = document.createElement("a");
        timedLink.href = "#timed";
        untimedLink.href = "#";
        timerLinks.textContent = "Timer:"
        timedLink.textContent = "On"
        untimedLink.textContent = "Off"
        timerLinks.classList.add("timerLinks");
        timerLinks.appendChild(timedLink);
        timerLinks.appendChild(untimedLink);
        document.body.appendChild(timerLinks);

        var lastTimer = null;
        var lines = document.getElementsByClassName("line");

        var parseDate = function(dateString) {
            var dateRegex = /([0-9]+)-([0-9]+)-([0-9]+) ([0-9]{2}):([0-9]{2}):([0-9]{2})/;
            dateMatch = dateRegex.exec(dateString);
            if(dateMatch == null) {
                return null;
            } else {
                return new Date(
                        parseInt(dateMatch[1]),
                        parseInt(dateMatch[2]),
                        parseInt(dateMatch[3]),
                        parseInt(dateMatch[4]),
                        parseInt(dateMatch[5]),
                        parseInt(dateMatch[6]));
            }
        }

        var initFunction = function() {
            if(lastTimer != null) {
                clearTimeout(lastTimer);
            }

            if(location.hash == "#timed") {
                timedLink.classList.add("active");
                untimedLink.classList.remove("active");

                for(var i = 0; i < lines.length; i++) {
                    lines[i].classList.add("timeHidden");
                }

                var showNextLine = function() {
                    lines[this].classList.remove("timeHidden");
                    if(this < lines.length) {
                        setTimeout(showNextLine.bind(this+1), parseDate(lines[this+1].getElementsByClassName("timestamp")[0].textContent) - parseDate(lines[this].getElementsByClassName("timestamp")[0].textContent));
                    }
                };

                showNextLine.bind(0)();
            } else {
                untimedLink.classList.add("active");
                timedLink.classList.remove("active");

                for(var i = 0; i < lines.length; i++) {
                    lines[i].classList.remove("timeHidden");
                }
            }
        };

        window.addEventListener("hashchange", initFunction);
        initFunction();
    </script>"""

def render_html(line_generator, args):
    yield template_header.format(log_name = args.log_name)

    for (timestamp, message) in line_generator:
        if args.keep_timestamp:
            if args.keep_date:
                time_format="%Y-%m-%d %H:%M:%S"
            else:
                time_format="%H:%M:%S"
            line_base = template_line_timestamp
        else:
            line_base = template_line

        if isinstance(message, messages.PrivMsg):
            yield line_base["gutter"].format(
                    msg_type="privmsg",
                    timestamp=timestamp.strftime(time_format),
                    gutter="""&lt;<span class="username">{0}</span>&gt;""".format(message.username),
                    text=message.text)
        elif isinstance(message, messages.Action):
            yield line_base["no_gutter"].format(
                    msg_type="action",
                    timestamp=timestamp.strftime(time_format),
                    text="""<span class="username">{0}</span> {1}""".format(message.username, message.text))
        elif isinstance(message, messages.Notice):
            yield line_base["gutter"].format(
                    msg_type="notice",
                    timestamp=timestamp.strftime(time_format),
                    gutter="""-<span class="username">{0}</span>-""".format(message.username),
                    text=message.text)
        elif isinstance(message, messages.Join):
            yield line_base["no_gutter"].format(
                    msg_type="join",
                    timestamp=timestamp.strftime(time_format),
                    text="""<span class="username">{0}</span> joined""".format(message.username))
        elif isinstance(message, messages.Part):
            yield line_base["no_gutter"].format(
                    msg_type="part",
                    timestamp=timestamp.strftime(time_format),
                    text="""<span class="username">{0}</span> left""".format(message.username))
        elif isinstance(message, messages.Quit):
            yield line_base["no_gutter"].format(
                    msg_type="quit",
                    timestamp=timestamp.strftime(time_format),
                    text="""<span class="username">{0}</span> quit""".format(message.username))
        elif isinstance(message, messages.System):
            yield line_base["no_gutter"].format(
                    msg_type="system",
                    timestamp=timestamp.strftime(time_format),
                    text=message.text)

    if args.add_timer:  # TODO: correctly handle date parsing in the case of --drop-(date|timestamp)
        yield template_footer.format(script=template_script)
    else:
        yield template_footer.format(script="")

register_renderer(render_html, "html", "emits HTML",
        (('-t', '--timer', {
            'action': 'store_true',
            'dest': 'add_timer',
            'help': '''Include a javascript-based timer. Incurs some significant
                extra load time on long logs.''',
            }),
         ('-n', '--log-name', {
            'action': 'store',
            'dest': 'log_name',
            'default': 'Prettified Log',
            'help': '''Name to use for the log's title. If not provided,
            "Prettified Log" will be used.''',
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
        ))
