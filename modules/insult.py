#!/usr/bin/env python
# encoding: utf-8

import threading
import time
import random
import re

nouns = [
    'jerk',
    'butthead',
    'bonehead',
    'dunce',
    'moron',
    'dick',
    'asshole',
    'bitch',
    'fuck face',
    'windows user',
    'fucking fuck',
    'dick sucker',
    'cock block',
]

adjectives = [
    'smelly',
    'ugly',
    'shitty',
    'black',
    'crappy',
    'bloated',
    'retarded',
    'fucking',
    'motherfucking',
    'son of a',
]

def insult(phenny, input):
    matches = re.search(insult.rule, input.group())
    if not matches:
        return
    target = matches.groups()[0]
    msg = "%s is a %s %s" % (
            target,
            random.choice(adjectives),
            random.choice(nouns),
        )
    phenny.say(" ".join([x.strip() for x in msg.split(" ") if not x in ["", " "]]))
insult.rule = r"^!insult (.*)$"
insult.priority = "medium"
