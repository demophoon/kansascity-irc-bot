import re
import logging
import unicodedata

from modules import (
    quote,
    game_tools,
)

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class phenny_fake(object):

    """A fake phenny for importing the logs."""

    def __init__(self):
        """@todo: to be defined1. """

    def say(self, msg):
        print "Demophoon: %s" % msg


class message_handler(str):

    """Docstring for message_handler. """

    nick = None
    sender = None
    message = None

    def group(self):
        return self.message


def main():
    regex = re.compile(r"^\d+:\d+\W+<\W?([a-zA-Z0-9-_]+)\W\s(.*)$", re.MULTILINE)

    logfiles = [
        ("/home/britt/.irssi/logs/freenode/#r_kansascity.log", "#r/kansascity"),
        ("/home/britt/.irssi/logs/freenode/##kcshoptalk.log", "##kcshoptalk"),
    ]

    for filename, roomname in logfiles:
        log = open(filename).read()
        matches = [x for x in regex.findall(log) if not x[0] == "demophoon"]

        p = phenny_fake()

        valid_methods = [
            quote.logger,
            quote.grab,
            quote.add_point,
            quote.fetch_quote,
            quote.random_user_quote,
            quote.no_context,
            quote.random_quote,
            quote.rimshot,
            game_tools.coin_flip,
            game_tools.this_or_that,
        ]

        for match in matches:
            msg = match[1].decode("ascii", "ignore")
            msg = unicodedata.normalize("NFKD", msg)
            m = message_handler(msg)
            m.nick = match[0]
            m.sender = roomname
            m.message = match[1]

            for method in valid_methods:
                if re.match(method.rule, msg):
                    if not method == quote.logger:
                        print "%s: %s" % (m.nick, m)
                    method(p, m)

    exit(0)


if __name__ == '__main__':
    main()
