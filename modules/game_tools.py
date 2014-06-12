#!/usr/bin/env python
# encoding: utf-8

import random


def coin_flip(phenny, input):
    phenny.say(random.choice(["Heads.", "Tails."]))
coin_flip.rule = r"^!coinflip$"
coin_flip.priority = "medium"


def this_or_that(phenny, input):
    target = input.groups()[0]
    phenny.say(random.choice(target.split(" or ")))
this_or_that.rule = r".*$nickname\W?([a-zA-Z0-9\-_, ]+ or [a-zA-Z0-9\-_, ]+)\W*$"
this_or_that.priority = "medium"


#def alarm(phenny, input):
#    phenny.say(random.choice(["Heads.", "Tails."]))

#alarm.rule = r"^!coinflip$"
#alarm.priority = "medium"
