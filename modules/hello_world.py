#!/usr/bin/env python

import threading
import time
import random


def helloworld(phenny, input):
    phenny.say("Hello World!")
#helloworld.commands = ['hello']
#helloworld.priority = 'medium'


def high_five(phenny, input):
    phenny.say("gives " + input.nick + " a glorious high five")
#high_five.rule = r"^gives $nickname a high five"
#high_five.priority = 'medium'


def setup(phenny):
    #thread = HighFiveThread(phenny).start()
    pass


class HighFiveThread(threading.Thread):

    def __init__(self, phenny):
        """docstring for __init__"""
        self.phenny = phenny
        self.high_five_types = [
            (
                "holds hand up for a high five",
                "high fives %{user}s"
            ),
        ]
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(random.randint(30, 300))
            self.phenny.say(random.choice(self.high_five_types)[0])

