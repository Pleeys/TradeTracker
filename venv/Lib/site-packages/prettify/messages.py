#!/usr/bin/env python
from __future__ import unicode_literals

class BaseMessage(object):
    pass

class PrivMsg(BaseMessage):
    def __init__(self, username, text):
        self.username = username
        self.text = text

class Action(BaseMessage):
    def __init__(self, username, text):
        self.username = username
        self.text = text

class Join(BaseMessage):
    def __init__(self, username):
        self.username = username

class Part(BaseMessage):
    def __init__(self, username):
        self.username = username

class Quit(BaseMessage):
    def __init__(self, username):
        self.username = username

class Notice(BaseMessage):
    def __init__(self, username, text):
        self.username = username
        self.text = text

class System(BaseMessage):
    def __init__(self, text):
        self.text = text
