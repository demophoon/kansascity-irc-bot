import re
import logging
import unicodedata
import datetime

from modules import (
    quote,
    game_tools,
)

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class phenny_fake(object):

    """A fake phenny for importing the logs."""

    nick = "demophoon"

    def __init__(self):
        """@todo: to be defined1. """

    def say(self, msg):
        print "Demophoon: %s" % msg


class message_handler(str):

    """Docstring for message_handler. """

    nick = None
    sender = None
    message = None
    owner = None

    def __init__(self, *args, **kwargs):
        pass

    def group(self):
        return self.message

    def groups(self):
        pass


def main():
    msg_regex = re.compile(r"^(\d+:\d+)\W+<\W?([a-zA-Z0-9-_]+)\W\s(.*)$")

    # --- Log opened Wed Apr 09 15:43:47 2014
    # --- Day changed Thu Apr 10 2014
    date_regex = re.compile(r"^--- \w+ \w+ \w+ (\w+) (\d+).*(\d\d\d\d)")

    logfiles = [
        ("/home/britt/.irssi/logs/freenode/#r_kansascity.log", "#r/kansascity"),
        ("/home/britt/.irssi/logs/freenode/##kcshoptalk.log", "##kcshoptalk"),
        ("/home/britt/.irssi/logs/freenode/##brittslittlesliceofheaven.log", "##brittslittlesliceofheaven"),
        ("/home/britt/.irssi/logs/freenode/#reddit-stlouis.log", "#reddit-stlouis"),
    ]

    month_translation = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }


    p = phenny_fake()

    valid_methods = [
        quote.logger,
        quote.grab,
        quote.give_respect,
        quote.user_point,
        quote.transfer,
        #quote.fetch_quote,
        #quote.random_user_quote,
        #quote.no_context,
        #quote.random_quote,
        #quote.rimshot,
        #quote.word_count,
        #quote.points,
        #quote.trending,
        #quote.unsad,
        #quote.sandwich,
        #quote.your_mom,
        #game_tools.coin_flip,
        #game_tools.this_or_that,
    ]

    valid_methods = [(re.compile(x.rule), x) for x in valid_methods]

    for filename, roomname in logfiles:

        sender = roomname
        with open(filename, "r+") as log:
            current_day = datetime.datetime(2000, 1, 1)
            for line in log:
                msg_matches = msg_regex.search(line)
                if msg_matches:
                    nick = msg_matches.groups()[1]

                    if nick == "demophoon":
                        continue

                    message = msg_matches.groups()[2]
                    hours = int(msg_matches.groups()[0].split(":")[0])
                    minutes = int(msg_matches.groups()[0].split(":")[1])
                    date = current_day + datetime.timedelta(
                        hours=hours, minutes=minutes)

                    quote.get_current_time = lambda: date

                    msg = message.decode("ascii", "ignore")
                    msg = unicodedata.normalize("NFKD", msg)
                    m = message_handler(msg)
                    m.nick = nick
                    m.sender = sender
                    m.message = message

                    for method in valid_methods:
                        if method[0].match(msg):
                            m.groups = lambda: method[0].match(msg).groups()
                            if not method[1] == quote.logger:
                                print "%s <%s>: %s" % (str(date), m.nick, m)
                            method[1](p, m)

                else:
                    date_matches = date_regex.match(line)
                    if not date_matches:
                        continue
                    year = int(date_matches.groups()[2])
                    day = int(date_matches.groups()[1])
                    month = int(month_translation[date_matches.groups()[0].lower()])
                    current_day = datetime.datetime(year, month, day)


if __name__ == '__main__':
    main()
