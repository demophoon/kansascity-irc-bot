#!/usr/bin/env python
# encoding: utf-8

ignored_nicks = [
]

import datetime
import random
import re
import collections

# ----- Models -----

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()


def check_ignore(phenny, input):
    nick = input.nick
    for ignored_nick in ignored_nicks:
        if re.search(re.compile(ignored_nick, re.IGNORECASE), nick):
            return True


def smart_ignore(fn):
    def callable(phenny, input):
        if check_ignore(phenny, input):
            return None
        return fn(phenny, input)
    return callable


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    room_id = Column(Integer, ForeignKey("room.id"))
    body = Column(String(convert_unicode=True))
    created_at = Column(DateTime)

    def __init__(self):
        self.created_at = datetime.datetime.now()


class Room(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    messages = relationship("Message", backref="room")


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    nick = Column(String)
    access = Column(String)
    messages = relationship("Message", backref="user")


class Quote(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("message.id"))
    message = relationship("Message", backref="quotes")
    created_at = Column(DateTime)

    def __init__(self):
        self.created_at = datetime.datetime.now()


class Point(Base):
    __tablename__ = 'point'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    type = Column(String)
    created_at = Column(DateTime)
    value = Column(Integer)

    user = relationship("User", backref="points")

    def __init__(self, type, user_id, value=1):
        self.created_at = datetime.datetime.now()
        self.type = type
        self.user_id = user_id
        self.value = value


class Audit(Base):
    __tablename__ = 'audit'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    message_id = Column(Integer, ForeignKey("message.id"))

    user = relationship("User", backref="audits")
    message = relationship("Message", backref="audit")


# ----- end models -

DBSession = None

engine = create_engine("sqlite:///irclog.db")
DBSession = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)

high_five_avail = False
current_high_five = None

def setup(phenny):
    global DBSession
    global Base
    pass


def action(msg):
    msg = '\x01ACTION %s\x01' % msg
    return msg

highfives = [
    {
        "type": "raises his hand for a high five.",
        "value": 1,
    },
    {
        "type": "throws his hand down for a low five.",
        "value": 1,
    },
    {
        "type": "shoots his hand up for a high five.",
        "value": 1,
    },
    {
        "type": "throws up his hand and waits for a high five.",
        "value": 1,
    },
    {
        "type": "throws down his hand and waits for a low five.",
        "value": 1,
    },
    {
        "type": "throws hand up in the air for a moist high five!",
        "value": 1,
    },
    {
        "type": "throws both hands in the air for a double high five!",
        "value": 2,
        "response": "gives %(nick)s a double high five and two %(item)s seeing that they not have %(points)d %(item)s.",
    },
    {
        "type": "puts his ass in the air for an ass five",
        "value": -1,
        "response": "takes a beer from %(nick)s. What the hell %(nick)s?!?",
    },
]


def ask_for_highfive(phenny):
    global high_five_avail
    global current_high_five
    global highfives
    high_five_avail = True
    current_high_five = random.choice(highfives)
    phenny.say(action(current_high_five['type']))


def logger(phenny, input):
    if not DBSession.query(User).filter(User.nick == input.nick).first():
        new_user = User()
        new_user.nick = input.nick
        DBSession.add(new_user)
    if not DBSession.query(Room).filter(Room.name == input.sender).first():
        new_room = Room()
        new_room.name = input.sender
        DBSession.add(new_room)
    user_id = DBSession.query(User).filter(User.nick == input.nick).first()
    room_id = DBSession.query(Room).filter(
        Room.name == input.sender).first()
    msg = Message()
    msg.body = input
    msg.user_id = user_id.id
    msg.room_id = room_id.id
    DBSession.add(msg)
    DBSession.flush()
    DBSession.commit()

    if u"┻━" in input and u"━┻" in input:
        table_length = input.count(u"━")
        table_str = u""
        if table_length > 10:
            table_str = u"━*%d" % table_length
        else:
            table_str = u"".join([u"━" for _ in range(table_length)])
        phenny.say(u"┬" + table_str + u"┬﻿ ノ( ゜-゜ノ)")
    elif not(high_five_avail) and random.choice(range(500)) == 0:
        ask_for_highfive(phenny)

logger.rule = r'(.*)'
logger.priority = 'low'
logger.thread = False


grab_yourself_warnings = [
    "You cannot grab yourself sicko!",
    "Get a room.",
    "You gotta grab someone else.",
    "You wouldn't grab yourself in public.",
    "Think about what you are doing before you do that.",
    "Lets think about this now...",
    "You cannot grab yourself. At least not here...",
    "That feels nice doesn't it?",
    "No grabbing yourself in here.",
    "You cannot grab yourself.",
    "Want a tissue?",
    "Give someone else a grab.",
    "It's better when someone else grabs you.",
]


@smart_ignore
def grab(phenny, input):
    matches = re.search(grab.rule, input.group())
    target = matches.groups()[0]
    if target == input.nick:
        phenny.say(random.choice(grab_yourself_warnings))
    elif target == "demophoon":
        phenny.say("I cannot let you do that.")
    else:
        message = DBSession.query(Message).join(User).join(Room).filter(
            User.nick == target
        ).filter(
            Room.name == input.sender
        ).order_by(Message.created_at.desc()).first()
        if not message:
            phenny.say("I don't remember what %s said. :(" % target)
        else:
            new_quote = Quote()
            new_quote.message_id = message.id
            DBSession.add(new_quote)
            DBSession.flush()
            DBSession.commit()
            phenny.say("Quote %d added" % new_quote.id)


grab.rule = r'^!grab ([a-zA-Z0-9-_]+)'
grab.priority = 'medium'
grab.thread = False


@smart_ignore
def random_quote(phenny, input):
    quote = DBSession.query(Quote).join(
        Message
    ).join(Room).join(User).filter(
        Room.name == input.sender
    ).order_by(
        sa.func.random()
    ).first()
    if quote:
        phenny.say("Quote #%d from %s: '%s'" % (
            quote.id, quote.message.user.nick, quote.message.body))

random_quote.rule = r'^!random$'
random_quote.priority = 'medium'
random_quote.thread = False


@smart_ignore
def no_context(phenny, input):
    msg = DBSession.query(Message).join(Room).filter(
        Room.name == input.sender
    ).order_by(
        sa.func.random()
    ).first()
    phenny.say(msg.body)
no_context.rule = r'^!nocontext$'
no_context.priority = 'medium'
no_context.thread = False


@smart_ignore
def random_user_quote(phenny, input):
    matches = re.search(random_user_quote.rule, input.group())
    target = matches.groups()[0]
    quote = DBSession.query(Quote).join(
        Message
    ).join(User).join(Room).filter(
        Room.name == input.sender
    ).filter(
        User.nick == target
    ).order_by(
        sa.func.random()
    ).first()
    if quote:
        phenny.say("Quote #%d from %s: '%s'" % (
            quote.id, quote.message.user.nick, quote.message.body))
    else:
        phenny.say("No quotes from %s" % target)

random_user_quote.rule = r'^!random ([a-zA-Z0-9-_]+)'
random_user_quote.priority = 'medium'
random_user_quote.thread = False


@smart_ignore
def fetch_quote(phenny, input):
    matches = re.search(fetch_quote.rule, input.group())
    target = matches.groups()[0]
    quote = DBSession.query(Quote).join(
        Message
    ).join(User).join(Room).filter(
        Room.name == input.sender
    ).filter(
        Quote.id == int(target)
    ).first()
    if quote:
        phenny.say("Quote #%d from %s: '%s'" % (
            quote.id, quote.message.user.nick, quote.message.body))
    else:
        phenny.say("Quote does not exist.")
fetch_quote.rule = r'^!quote (\d+)$'
fetch_quote.priority = 'medium'
fetch_quote.thread = False


@smart_ignore
def word_count(phenny, input):
    matches = re.search(word_count.rule, input.group())
    target = matches.groups()[0]
    wc = " ".join([x.body for x in DBSession.query(Message).join(
        Room).filter(Room.name == input.sender).all()]).lower().count(target.lower())
    phenny.say("%s: Word count for %s: %d" % (
        input.nick,
        target,
        wc,
    ))
word_count.rule = r'^!wc (.*)$'
word_count.priority = 'medium'
word_count.thread = False


#def leaderboard(phenny, input):
#    user_points = DBSession.query(sa.func.sum(Point.value)).join(User).filter(
#        Point.type == 'respect'
#    ).filter(User.nick == input.nick).all()
#    phenny.say("%s now has %d respect." % (user_id.nick, user_points))
#leaderboard.rule = r'^!leaderboard$'
#leaderboard.priority = 'medium'
#leaderboard.thread = False


@smart_ignore
def give_highfive(phenny, input):
    global high_five_avail
    global current_high_five
    if not high_five_avail:
        return

    matches = re.search(give_highfive.rule, input.group())
    highfive_type = matches.groups()[0]

    regex = re.compile(" an? ([a-zA-Z- ]+) five")
    r = regex.search(current_high_five['type'])
    matching_type = r.groups()[0]
    if not highfive_type == matching_type:
        print highfive_type, matching_type
        return

    user_id = DBSession.query(User).filter(User.nick == input.nick).first()
    if user_id:
        DBSession.add(Point("high five", user_id.id, current_high_five['value']))
        DBSession.flush()
        DBSession.commit()
        points = DBSession.query(Point).join(
            User
        ).filter(
            Point.type == "high five"
        ).filter(User.nick == input.nick).all()
        user_points = 0
        for point in points:
            user_points += point.value

        item = "beers"
        if user_points == 1:
            item = "beer"
        a_an = "a"
        if highfive_type[0] in ['a', 'e', 'i', 'o', 'u']:
            a_an = "an"
        if "response" in current_high_five:
            hf = current_high_five['response']
        else:
            hf = "gives %(nick)s %(a_an)s %(type)s five and sees that they have %(points)d %(item)s"
        hf %= {
            "nick": input.nick,
            "a_an": a_an,
            "type": highfive_type,
            "points": user_points,
            "item": item,
        }
        phenny.msg(input.sender, action(hf))
        high_five_avail = False
        current_high_five = None
give_highfive.rule = r'^\x01ACTION gives demophoon an? ([a-zA-Z- ]+) five'
give_highfive.priority = 'medium'
give_highfive.thread = False


@smart_ignore
def give_user_point(phenny, input):
    banned_types = ['respect', 'high five']
    matches = re.search(give_user_point.rule, input.group())
    target = matches.groups()[0]
    quantity = matches.groups()[1]
    point_type = matches.groups()[2].lower()
    if quantity.lower() in ["a", "an"]:
        quantity = 1
    else:
        quantity = int(quantity)
    if quantity > 1:
        if point_type.endswith("es"):
            point_type = point_type[:-2]
        elif point_type.endswith("s"):
            point_type = point_type[:-1]
    if abs(quantity) > 10:
        phenny.say("Woah there buddy, slow down.")
        return
    if not(target == input.nick) and point_type not in banned_types:
        user_id = DBSession.query(User).filter(User.nick == target).first()
        if user_id:
            DBSession.add(Point(point_type, user_id.id, quantity))
            DBSession.flush()
            DBSession.commit()
            points = DBSession.query(Point).join(
                User
            ).filter(
                Point.type == point_type
            ).filter(User.nick == target).all()
            user_points = 0
            for point in points:
                user_points += point.value
            if not(user_points == 1):
                if point_type.endswith("es"):
                    pass
                elif point_type.endswith("s"):
                    point_type += "es"
                else:
                    point_type += "s"
            if not user_points == 1:
                phenny.say("%s has %d %s." % (user_id.nick, user_points, point_type))
            else:
                phenny.say("%s has %d %s." % (user_id.nick, user_points, point_type))
give_user_point.rule = r'^!give ([a-zA-Z0-9-_]+) (an?|-?\d+) ([a-zA-Z0-9, ]+)'
give_user_point.priority = 'medium'
give_user_point.thread = False


@smart_ignore
def add_point(phenny, input):
    matches = re.search(add_point.rule, input.group())
    target = matches.groups()[0]
    if not(target == input.nick) or target == "demophoon":
        user_id = DBSession.query(User).filter(User.nick == target).first()
        if user_id:
            DBSession.add(Point("respect", user_id.id))
            DBSession.flush()
            DBSession.commit()
            points = DBSession.query(Point).join(
                User
            ).filter(
                Point.type == "respect"
            ).filter(User.nick == target).all()
            user_points = 0
            for point in points:
                user_points += point.value
            phenny.say("%s now has %d respect." % (user_id.nick, user_points))
add_point.rule = r"([a-zA-Z0-9_]+)\+\+"
add_point.priority = 'medium'
add_point.thread = False


@smart_ignore
def remove_point(phenny, input):
    matches = re.search(remove_point.rule, input.group())
    target = matches.groups()[0]
    if not(target == input.nick) or target == "demophoon":
        user_id = DBSession.query(User).filter(User.nick == target).first()
        if user_id:
            DBSession.add(Point("respect", user_id.id, -1))
            DBSession.flush()
            DBSession.commit()
            points = DBSession.query(Point).join(
                User
            ).filter(
                Point.type == "respect"
            ).filter(User.nick == target).all()
            user_points = 0
            for point in points:
                user_points += point.value
            phenny.say("%s now has %d respect." % (user_id.nick, user_points))
remove_point.rule = r"([a-zA-Z0-9_]+)--"
remove_point.priority = 'medium'
remove_point.thread = False


@smart_ignore
def trending(phenny, input):
    #matches = re.search(trending.rule, input.group())
    #target = matches.groups()[0]
    start_time = datetime.datetime.now() - datetime.timedelta(hours=4)
    words = [
        word for word in
        ' '.join([x.body for x in DBSession.query(Message).join(Room).filter(
            Room.name == input.sender
        ).filter(
            Message.created_at > start_time
        ).all()]).lower().split(' ') if word not in [
            "the", "of", "and", "a", "to", "in", "is", "you", "that",
            "it", "he", "was", "for", "on", "are", "as", "with", "his",
            "they", "I", "at", "be", "this", "have", "from", "or",
            "one", "had", "by", "word", "but", "not", "what", "all",
            "were", "we", "when", "your", "can", "said", "there", "use",
            "an", "each", "which", "she", "do", "how", "their", "if",
            "will", "up", "other", "about", "out", "many", "then",
            "them", "these", "so", "some", "her", "would", "make", "like",
            "him", "into", "time", "has", "look", "two", "more", "write",
            "go", "see", "number", "no", "way", "could", "people", "my",
            "than", "first", "water", "been", "call", "who", "oil", "its",
            "now", "find", "long", "down", "day", "did", "get", "come",
            "made", "may", "part", "it's", "", "!grab", "!nocontext",
            "!quote", "!random", "i", "me", "am", "just", "!trending",
            "lol", "!give",
        ]
    ]

    most_common = collections.Counter(words).most_common(10)

    phenny.say(
        "Trending over last 4 hours: %s " %
        ', '.join([
            "%s (%d)" % word for word in most_common
        ])
    )
trending.rule = r"^!trending"
trending.priority = 'medium'
trending.thread = False


@smart_ignore
def unsad(phenny, input):
    phenny.say("%s*" % random.choice([
        ":)",
        ":-)",
        "(:",
        "(-:",
        ":D",
        ":-D",
        ":]",
        ":-]",
    ]))

unsad.rule = r'(:\W*[\(\[\{]|[D\)\]\}]\W*:)'
unsad.priority = 'medium'


@smart_ignore
def sandwich(phenny, input):
    phenny.say("Shut your whore mouth and make your own sandwich")
sandwich.rule = "^demophoon\W+ make me a (sandwich|sammich)"
sandwich.priority = 'medium'


@smart_ignore
def rimshot(phenny, input):
    phenny.say("Buh dum tsh")
rimshot.rule = "^!rimshot"
rimshot.priority = 'medium'


@smart_ignore
def your_mom(phenny, input):
    matches = re.search(your_mom.rule, input.group())
    msg = "Your mom %s %s." % (
        matches.groups()[0],
        matches.groups()[1],
    )
    print msg
    if random.choice(range(7)) == 0:
        phenny.say(msg)
your_mom.rule = r"^.* (is|has|used to be) (\w+)\W?$"
your_mom.priority = 'medium'
