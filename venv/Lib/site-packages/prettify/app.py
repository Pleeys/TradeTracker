#!/usr/bin/env python
from __future__ import unicode_literals, print_function

readers = {}
renderers = {}

def register_reader(reader_fn, reader_name, reader_desc="", reader_options=()):
    readers[reader_name] = (reader_fn, reader_desc, reader_options)

def register_renderer(renderer_fn, renderer_name, renderer_desc="", renderer_options=()):
    renderers[renderer_name] = (renderer_fn, renderer_desc, renderer_options)

def prettify_log(ugly_log, reader, reader_args, renderer, renderer_args,
        ignore_types):
    if ignore_types is not None:
        def wrapped_reader():
            for line in reader(ugly_log, reader_args):
                if not type(line[1]) in ignore_types:
                    yield line
        return renderer(wrapped_reader(), renderer_args)
    else:
        return renderer(reader(ugly_log, reader_args), renderer_args)

def run():
    import argparse, sys, prettify.reader, prettify.renderer, prettify.messages

    parser = argparse.ArgumentParser(description='''Prettify an IRC log.''')
    parser.add_argument('-r', '--reader', action='store', default='weechat',
            choices=readers.keys(), help='''Reader to use for parsing the
            provided log.''', dest='reader')
    parser.add_argument('-rh', '--reader-help', action='store_true',
            help='''Show help for the active reader.''', dest='reader_help')
    parser.add_argument('-R', '--renderer', action='store', default='plaintext',
            choices=renderers.keys(), help='''Renderer to use for printing the
            prettified log.''', dest='renderer')
    parser.add_argument('-Rh', '--renderer-help', action='store_true',
            help='''Show help for the active renderer.''', dest='renderer_help')
    parser.add_argument('-i', '--input-file', action='store', default=sys.stdin,
            type=argparse.FileType('r'), help='''Log file to prettify (STDIN
            will be used if this is not given).''', dest="infile")
    parser.add_argument('-o', '--output-file', action='store',
            default=sys.stdout, type=argparse.FileType('w'), help='''Output file
            to write to (STDOUT will be used if this is not given).''',
            dest='outfile')
    parser.add_argument('--ignore-privmsg', action='append_const',
            const=prettify.messages.PrivMsg, dest="ignore_types",
            help='''Drop PRIVMSG lines (regular chat and PMs).''')
    parser.add_argument('--ignore-action', action='append_const',
            const=prettify.messages.Action, dest="ignore_types",
            help='''Drop action lines (/me actions).''')
    parser.add_argument('--ignore-notice', action='append_const',
            const=prettify.messages.Notice, dest="ignore_types",
            help='''Drop notice lines.''')
    parser.add_argument('--ignore-join', action='append_const',
            const=prettify.messages.Join, dest="ignore_types",
            help='''Drop join lines.''')
    parser.add_argument('--ignore-part', action='append_const',
            const=prettify.messages.Part, dest="ignore_types",
            help='''Drop part lines.''')
    parser.add_argument('--ignore-quit', action='append_const',
            const=prettify.messages.Quit, dest="ignore_types",
            help='''Drop quit lines.''')
    parser.add_argument('--ignore-system', action='append_const',
            const=prettify.messages.System, dest="ignore_types",
            help='''Drop system message lines.''')
    args, unknown_args = parser.parse_known_args()

    reader_parser = argparse.ArgumentParser(description=readers[args.reader][1])
    for option in readers[args.reader][2]:
        reader_parser.add_argument(*option[:-1], **option[-1])
    if args.reader_help:
        reader_parser.parse_args(['-h'])
    else:
        reader_args, unknown_args = reader_parser.parse_known_args(unknown_args)

    renderer_parser = argparse.ArgumentParser(description=renderers[args.renderer][1])
    for option in renderers[args.renderer][2]:
        renderer_parser.add_argument(*option[:-1], **option[-1])
    if args.renderer_help:
        renderer_parser.parse_args(['-h'])
    else:
        renderer_args = renderer_parser.parse_args(unknown_args)

    if not (args.reader_help or args.renderer_help):
        for line in prettify_log(args.infile,
                readers[args.reader][0], reader_args,
                renderers[args.renderer][0], renderer_args, args.ignore_types):
            args.outfile.write(line)
