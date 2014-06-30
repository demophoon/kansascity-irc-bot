#!/usr/bin/env python
# encoding: utf-8

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
    not_
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()


def get_current_time():
    return datetime.datetime.now()

ignored_nicks = [
    ".*bot",
]


def check_ignore(phenny, input):
    ignore = False
    if not input.sender.startswith("#"):
        ignore = True
    for ignored_nick in ignored_nicks:
        if re.search(re.compile(ignored_nick, re.IGNORECASE), input.nick):
            ignore = True
            print "%s is ignored by rule %s" % (
                input.nick,
                ignored_nick
            )
    if input.owner:
        ignore = False
    return ignore


def smart_ignore(fn):
    def callable(phenny, input):
        if check_ignore(phenny, input):
            return None
        if input.sender in limited_channels:
            if limited_channels[input.sender].get('allowed'):
                if fn in [x._original for x in limited_channels[input.sender]['allowed']]:
                    return fn
                return None
            if fn in [x._original for x in limited_channels[input.sender]['ignored']]:
                return None
        return fn(phenny, input)
    callable._original = fn
    return callable


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    room_id = Column(Integer, ForeignKey("room.id"))
    body = Column(String(convert_unicode=True))
    created_at = Column(DateTime)

    def __init__(self):
        self.created_at = get_current_time()


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
    grabbed_by = Column(Integer, ForeignKey("user.id"))
    message = relationship("Message")
    who_grabbed = relationship("User", backref="quotes")
    created_at = Column(DateTime)

    def __init__(self):
        self.created_at = get_current_time()


class Point(Base):
    __tablename__ = 'point'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    awarded_by_id = Column(Integer, ForeignKey(User.id))
    type = Column(String)
    created_at = Column(DateTime)
    value = Column(Integer)

    user = relationship("User", backref="points", foreign_keys=user_id)
    awarded_by = relationship("User", backref="awarded_points", foreign_keys=awarded_by_id)

    def __init__(self, type, user_id, awarded_by_id, value=1):
        start_time = get_current_time() - datetime.timedelta(minutes=10)
        user = DBSession.query(User).filter(
            User.id == user_id
        ).first()
        if sum([x.value for x in user.points if x.created_at > start_time]) > 20:
            value = 0
        if sum([x.value for x in user.awarded_points if x.created_at > start_time]) > 20:
            value = 0
        self.created_at = get_current_time()
        self.type = type
        self.user_id = user_id
        self.awarded_by_id = awarded_by_id
        self.value = value


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    tagged_by_id = Column(Integer, ForeignKey(User.id))
    created_at = Column(DateTime)
    tagged = Column(Integer)

    user = relationship("User", backref="tags", foreign_keys=user_id)
    awarded_by = relationship("User", backref="tagged", foreign_keys=tagged_by_id)

    def __init__(self):
        self.created_at = get_current_time()


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
        "response": "gives %(nick)s a double high five and two %(item)s seeing that they now have %(points)d %(item)s.",
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

    if input.sender in limited_channels:
        return
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
    target = input.groups()[1]
    offset = input.groups()[2] or 0
    if target == input.nick:
        phenny.say(random.choice(grab_yourself_warnings))
    elif target == phenny.nick:
        phenny.say("I cannot let you do that.")
    else:
        message = DBSession.query(Message).join(User).join(Room).filter(
            User.nick.ilike("%s%%" % target)
        ).filter(
            Room.name == input.sender
        ).filter(
            not_(Message.body.like("!%"))
        ).order_by(Message.created_at.desc()).limit(1 + offset).all()
        if not message:
            phenny.say("I don't remember what %s said. :(" % target)
        else:
            message = message[int(offset)]
            grabber_user = DBSession.query(User).filter(
                User.nick.ilike("%s%%" % input.nick)
            ).first()
            new_quote = Quote()
            new_quote.message_id = message.id
            new_quote.grabbed_by = grabber_user.id
            DBSession.add(new_quote)
            DBSession.flush()
            DBSession.commit()
            phenny.say("Quote %d added" % new_quote.id)
grab.rule = r'^(!|\x01ACTION )grabs? ([a-zA-Z0-9-_]+)\s*-?([0-9]+)?'
grab.priority = 'medium'
grab.thread = False


@smart_ignore
def tag(phenny, input):
    target = input.groups()[1]
    offset = input.groups()[2] or 0
    if target == input.nick:
        phenny.say(random.choice(grab_yourself_warnings))
    elif target == phenny.nick:
        phenny.say("I cannot let you do that.")
    else:
        message = DBSession.query(Message).join(User).join(Room).filter(
            User.nick.ilike("%s%%" % target)
        ).filter(
            Room.name == input.sender
        ).filter(
            not_(Message.body.like("!%"))
        ).order_by(Message.created_at.desc()).all()
        if not message:
            phenny.say("I don't remember what %s said. :(" % target)
        else:
            message = message[int(offset)]
            grabber_user = DBSession.query(User).filter(
                User.nick.ilike("%s%%" % input.nick)
            ).first()
            new_quote = Quote()
            new_quote.message_id = message.id
            new_quote.grabbed_by = grabber_user.id
            DBSession.add(new_quote)
            DBSession.flush()
            DBSession.commit()
            phenny.say("Quote %d added" % new_quote.id)
grab.rule = r'^(!|\x01ACTION )grabs? ([a-zA-Z0-9-_]+)\s*-?([0-9]+)?'
grab.priority = 'medium'
grab.thread = False


@smart_ignore
def touch(phenny, input):
    target = input.groups()[2]
    target = random.choice(["lgebaur", "timfreund's monitor"])
    phenny.msg(input.sender, action("touches %s with a moist foot." % target))
touch.rule = r'^(!)touch(es)? ([a-zA-Z0-9-_]+)'
touch.priority = 'medium'


@smart_ignore
def random_quote(phenny, input):
    quote = DBSession.query(Quote).join(
        Message
    ).join(User).join(Room).filter(
        Room.name == input.sender
    ).order_by(
        sa.func.random()
    ).first()
    if quote:
        phenny.say("Quote #%d grabbed by %s: <%s> %s" % (
            quote.id,
            quote.who_grabbed.nick,
            quote.message.user.nick,
            quote.message.body
        ))

random_quote.rule = r'^!random$'
random_quote.priority = 'medium'
random_quote.thread = False


@smart_ignore
def no_context(phenny, input):
    if input.groups():
        target = input.groups()[0]
        msg = DBSession.query(Message).join(Room).filter(
            Room.name == input.sender
        ).filter(
            Message.body.ilike("%%%s%%" % target)
        )
    else:
        msg = DBSession.query(Message).join(Room).filter(
            Room.name == input.sender
        )
    msg = msg.filter(not_(Message.body.like("!%")))
    msg = msg.order_by(
        sa.func.random()
    ).first()
    if msg:
        phenny.say(msg.body)
no_context.rule = r'^!nocontext\s?(.*)'
no_context.priority = 'medium'
no_context.thread = False


@smart_ignore
def random_user_quote(phenny, input):
    target = input.groups()[0]
    quote = DBSession.query(Quote).join(
        Message
    ).join(User).join(Room).filter(
        Room.name == input.sender
    ).filter(
        User.nick.ilike("%s%%" % target)
    ).order_by(
        sa.func.random()
    ).first()
    if quote:
        phenny.say("Quote #%d grabbed by %s: <%s> %s" % (
            quote.id,
            quote.who_grabbed.nick,
            quote.message.user.nick,
            quote.message.body
        ))
    else:
        phenny.say("No quotes from %s" % target)

random_user_quote.rule = r'^!random ([a-zA-Z0-9-_]+)'
random_user_quote.priority = 'medium'
random_user_quote.thread = False


@smart_ignore
def fetch_quote(phenny, input):
    input = re.search(fetch_quote.rule, input.group())
    if not input:
        return
    target = input.groups()[0]
    quote = DBSession.query(Quote).join(
        Message
    ).join(User)
    if target.isdigit():
        quote = DBSession.query(Quote).filter(
            Quote.id == int(target)
        ).first()
    else:
        quote = quote.filter(
            Message.body.ilike("%%%s%%" % target)
        ).first()
    if quote:
        phenny.say("Quote #%d grabbed by %s: <%s> %s" % (
            quote.id,
            quote.who_grabbed.nick,
            quote.message.user.nick,
            quote.message.body
        ))
    else:
        phenny.say("Quote does not exist.")
fetch_quote.rule = r'^!quote (.*)'
fetch_quote.priority = 'medium'
fetch_quote.thread = False


@smart_ignore
def word_count(phenny, input):
    input = re.search(word_count.rule, input.group())
    if not input:
        return
    target = input.groups()[0]
    wc = " ".join([x.body for x in DBSession.query(
        Message
    ).join(
        Room
    ).filter(
        not_(Message.body.ilike("!%"))
    ).filter(
        Room.name == input.sender
    ).all()]).lower().count(target.lower())
    phenny.say("%s: Word count for %s: %d" % (
        input.nick,
        target,
        wc,
    ))
word_count.rule = r'^!wc (.*)$'
word_count.priority = 'medium'
word_count.thread = False


def points(phenny, input):
    input = re.search(points.rule, input.group())
    if not input:
        return
    target = input.groups()[1]
    if target.lower() in ["everyone", "everybody"]:
        all_points = sorted(DBSession.query(
            sa.func.sum(Point.value),
            Point.type,
            User.nick,
        ).join(User, Point.user_id == User.id).group_by(
            User.nick
        ).group_by(
            Point.type
        ).order_by(Point.value).all(), reverse=True)[:10]
        phenny.say("Top 10 for %s: %s" % (
            "Everybody",
            ", ".join(["%(nick)s (%(points)d: %(type)s)" % {
                "nick": x[2],
                "points": x[0],
                "type": x[1],
            } for x in all_points])
        ))
        return
    user = DBSession.query(User).filter(
        User.nick.ilike("%s%%" % target)
    ).first()
    if not user:
        return
    user_points = {}
    for pt in [(x.type, x.value) for x in user.points]:
        if pt[0] not in user_points:
            user_points[pt[0]] = 0
        user_points[pt[0]] += pt[1]
    user_points = collections.Counter(user_points)
    phenny.say("Top 10 for %s: %s" % (
        user.nick,
        ", ".join(["%s (%d)" % x for x in user_points.most_common(10)])
    ))
points.rule = r'^!(point|score|inventory)s? ([a-zA-Z0-9-_]+)'
points.priority = 'medium'
points.thread = False


def duration(seconds):
    d = datetime.datetime(1,1,1) + seconds
    fstr = ""
    if d.day - 1 > 0:
        if d.day - 1 == 1:
            fstr += "%d day " % (d.day - 1)
        else:
            fstr += "%d days " % (d.day - 1)
    if d.hour > 0:
        if d.hour == 1:
            fstr += "%d hour " % d.hour
        else:
            fstr += "%d hours " % d.hour
    if d.minute > 0:
        if d.minute == 1:
            fstr += "%d minute " % d.minute
        else:
            fstr += "%d minutes " % d.minute
    if d.second > 0:
        if d.second == 1:
            fstr += "%d second " % d.second
        else:
            fstr += "%d seconds " % d.second
    return fstr


def last_active(phenny, input):
    target = input.groups()[1]
    user = DBSession.query(User).join(Message).join(
        Room
    ).filter(
        Room.name == input.sender
    ).filter(
        User.nick.ilike("%s%%" % target)
    ).order_by(User.nick.asc()).first()
    message = DBSession.query(Message).join(User).join(
        Room
    ).filter(
        Room.name == input.sender
    ).filter(
        User.nick.ilike("%s%%" % target)
    ).order_by(Message.created_at.desc()).first()
    if not user:
        return
    if user.nick == input.nick:
        phenny.say("Stahp Et >:(")
        return
    delta = get_current_time() - message.created_at
    phenny.say("User %s last message was %sago: %s" % (
        user.nick,
        duration(delta),
        message.body,
    ))
last_active.rule = r'^!(active|last) ([a-zA-Z0-9-_]+)'
last_active.priority = 'medium'
last_active.thread = False


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

    input = re.search(give_highfive.rule, input.group())
    if not input:
        return
    highfive_type = input.groups()[0]

    regex = re.compile(" an? ([a-zA-Z- ]+) five")
    r = regex.search(current_high_five['type'])
    matching_type = r.groups()[0]
    if not highfive_type == matching_type:
        return

    user_id = DBSession.query(User).filter(User.nick == input.nick).first()
    awarded_by = user_id
    if user_id:
        DBSession.add(Point("high five", user_id.id, awarded_by.id, current_high_five['value']))
        DBSession.flush()
        DBSession.commit()
        points = DBSession.query(Point).join(
            User, Point.user_id == User.id
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
give_highfive.rule = r'^\x01ACTION gives $nickname an? ([a-zA-Z- ]+) five'
give_highfive.priority = 'medium'
give_highfive.thread = False


@smart_ignore
def user_point(phenny, input):
    matches = input
    modifier = 1
    if not matches or not matches.groups():
        return
    if matches.groups()[1] == "give":
        regex = r'gives? ([a-zA-Z0-9-_]+) (\w+|-?\d+) ([a-zA-Z0-9,\- ]+)'
        matches = re.search(regex, input.group())
        if not matches:
            return
        target = matches.groups()[0]
        quantity = matches.groups()[1]
        point_type = matches.groups()[2].lower()
    else:
        regex = r'take (\w+|-?\d+) ([a-zA-Z0-9,\- ]+) from ([a-zA-Z0-9-_]+)'
        matches = re.search(regex, input.group())
        if not matches:
            return
        target = matches.groups()[2]
        quantity = matches.groups()[0]
        point_type = matches.groups()[1].lower()
        modifier = -1

    banned_types = ['respect', 'high five']
    if point_type in banned_types:
        return

    doge = quantity in ["many", "so", "much", "such", "wow"]
    if quantity.lower() in ["a", "an", "another", "one", "the"]:
        quantity = 1
    elif quantity.lower() in ["some", "many", "much", "wow", "so", "such", "lotsa"]:
        quantity = random.choice(range(2,10))
    elif quantity.lower() in ["all"]:
        quantity = 10
        if point_type.split(" ")[0] == "the":
            point_type = " ".join(point_type.split(" ")[1:])
    else:
        try:
            quantity = int(quantity)
        except Exception:
            return
    if quantity > 1:
        if point_type.endswith("ies"):
            point_type = point_type[:-3] + "y"
        elif point_type.endswith("es"):
            point_type = point_type[:-2]
        elif point_type.endswith("s"):
            point_type = point_type[:-1]
    if abs(quantity) > 10:
        phenny.say("Woah there buddy, slow down.")
        return
    quantity *= modifier
    awarded_by = DBSession.query(User).filter(User.nick.ilike("%s%%" % input.nick)).first()
    if target.lower() in ["everyone", "everybody"]:
        start_time = get_current_time() - datetime.timedelta(hours=4)
        points = [Point(point_type, x.id, awarded_by.id, quantity) for x in DBSession.query(
            User
        ).join(Message).join(Room).filter(
            Room.name == input.sender
        ).filter(
            Message.created_at > start_time
        ).distinct().all()]
        DBSession.add_all(points)
        DBSession.flush()
        DBSession.commit()
        phenny.say("Done! ^.^")
    elif not(target == input.nick) and point_type not in banned_types:
        user_id = DBSession.query(User).filter(User.nick.ilike("%s%%" % target)).first()
        if user_id:
            DBSession.add(Point(point_type, user_id.id, awarded_by.id, quantity))
            DBSession.flush()
            DBSession.commit()
            points = DBSession.query(Point).join(
                User, Point.user_id == User.id
            ).filter(
                Point.type == point_type
            ).filter(User.nick.ilike("%s%%" % target)).all()
            user_points = 0
            for point in points:
                user_points += point.value
            if not(user_points == 1):
                if point_type.endswith("es"):
                    pass
                elif point_type.endswith("y"):
                    point_type = point_type[:-1] + "ies"
                elif point_type.endswith("s") or point_type.endswith("x"):
                    point_type += "es"
                else:
                    point_type += "s"
            message = "%s has %d %s." % (user_id.nick, user_points, point_type)
            if doge:
                message += random.choice([
                    " such %s." % point_type,
                    " so %s." % point_type,
                    " wow.",
                    " so amaze.",
                    " many %s." % point_type,
                ])
            phenny.say(message)
user_point.rule = r'^(!|\x01ACTION )(give|take)s? (.+)'
user_point.priority = 'medium'
user_point.thread = False


@smart_ignore
def give_respect(phenny, input):
    awarded_by = DBSession.query(User).filter(User.nick.ilike("%s%%" % input.nick)).first()
    words = input.split(" ")
    targets = []
    for identifier in ["++", "--"]:
        quanitity = 1
        if identifier == "--":
          quanitity = -1
        targets += [[(y, quanitity) for y in x.split(identifier) if y] for x in input.split(" ") if identifier in x]
    updates = []
    for target in set([x[0] for x in targets if any(x)]):
        if not(target[0] == input.nick) or target[0] == phenny.nick:
            user_id = DBSession.query(User).filter(User.nick.ilike("%s%%" % target[0])).first()
            if user_id:
                DBSession.add(Point("respect", user_id.id, awarded_by.id, target[1]))
                DBSession.flush()
                DBSession.commit()
                points = DBSession.query(Point).join(
                    User, Point.user_id == User.id
                ).filter(
                    Point.type == "respect"
                ).filter(User.nick.ilike("%s%%" % target[0])).all()
                user_points = 0
                for point in points:
                    user_points += point.value
                updates.append("%s now has %d respect." % (user_id.nick, user_points))
    phenny.say(" ".join(updates))
give_respect.rule = r".*(\+\+|--)"
give_respect.priority = 'medium'
give_respect.thread = False


@smart_ignore
def trending(phenny, input):
    target = 4
    if input.groups()[0]:
        target = int(input.groups()[0])
        if target > 99:
            target = 99
        if target < 0:
            target = 0
    ignore_list = [
        "the", "of", "and", "a", "to", "in", "is", "you", "that",
        "it", "he", "was", "for", "on", "are", "as", "with", "his",
        "they", "i", "at", "be", "this", "have", "from", "or",
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
        "!quote", "!random", "i've", "me", "am", "just", "!trending",
        "lol", "!give", "!wc", "\x01action", "!points", "i'm", "oh",
        "that's", "thats",
    ]
    ignore_list += [phenny.nick.lower(),
                    "%s:" % phenny.nick.lower(),
                    "%s," % phenny.nick.lower()]
    ignore_list += [x.nick.lower() for x in DBSession.query(User).all()]
    ignore_list += ["%s:" % x.nick.lower() for x in DBSession.query(User).all()]
    ignore_list += ["%s," % x.nick.lower() for x in DBSession.query(User).all()]
    start_time = get_current_time() - datetime.timedelta(hours=target)
    words = [
        word for word in
        ' '.join([x.body for x in DBSession.query(Message).join(Room).filter(
            Room.name == input.sender
        ).filter(
            Message.created_at > start_time
        ).all()]).lower().split(' ') if word not in ignore_list
    ]

    most_common = collections.Counter(words).most_common(10)

    hours = "hours"
    if target == 1:
        hours = "hour"
    phenny.say(
        "Trending over last %d %s: %s " % (
            target,
            hours,
            ', '.join([
                "%s (%d)" % word for word in most_common
            ]),
        )
    )
trending.rule = r"^!trending\s?(\d+)?"
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

unsad.rule = r'$^(:\W*[\(\[\{]|[D\)\]\}]\W*:)'
unsad.priority = 'medium'


@smart_ignore
def sandwich(phenny, input):
    phenny.say("Shut your whore mouth and make your own sandwich")
sandwich.rule = "^$nickname\W+ make me a (sandwich|sammich)"
sandwich.priority = 'medium'


@smart_ignore
def rimshot(phenny, input):
    phenny.say("Buh dum tsh")
rimshot.rule = "^(!|\x01ACTION )rimshot"
rimshot.priority = 'medium'


@smart_ignore
def sadtuba(phenny, input):
    phenny.say("http://www.sadtuba.com/")
sadtuba.rule = "^(!|\x01ACTION )(sadtuba|sadtrombone)"
sadtuba.priority = 'medium'


@smart_ignore
def command_help(phenny, input):
    phenny.say(random.choice([
        "You will have to get by on your own.",
        "nou.",
        "Help Not Implemented.",
        "http://nooooooooooooooo.com/",
        "The request is understood, but has been refused.",
        "Please try again later.",
    ]))
command_help.rule = "^!help"
command_help.priority = 'medium'


@smart_ignore
def pod_bay_doors(phenny, input):
    phenny.say("I'm sorry Dave, I'm afraid I can't do that")
pod_bay_doors.rule = "^!?open the pod bay doors(, $nickname)?"
pod_bay_doors.priority = 'medium'


@smart_ignore
def standup(phenny, input):
    phenny.say(action("stands up"))
standup.rule = "^will the real $nickname please stand up\??"
standup.priority = 'medium'


@smart_ignore
def pats(phenny, input):
    phenny.say(action(random.choice([
        "giggles and smiles",
        "smiles really big",
        "grins a little bit",
        "grins real big",
        "gives %s a hug" % input.nick,
    ])))
pats.rule = "\x01ACTION pats $nickname on the head"
pats.priority = 'medium'


@smart_ignore
def slaps(phenny, input):
    phenny.say(action("slaps %s" % input.groups()[1]))
slaps.rule = "^(!)slaps? (.*)"
slaps.priority = 'medium'


@smart_ignore
def ignore(phenny, input):
    global ignored_nicks
    if not input.owner:
        return
    ignored_nicks.append(input.groups()[0])
    print ignored_nicks
ignore.rule = "^!ignore (.*)"
ignore.priority = 'medium'


@smart_ignore
def unignore(phenny, input):
    global ignored_nicks
    if not input.owner:
        return
    ignored_nicks.remove(input.groups()[0])
    print ignored_nicks
unignore.rule = "^!unignore (.*)"
unignore.priority = 'medium'


@smart_ignore
def your_mom(phenny, input):
    if phenny.nick in input.lower():
        return
    msg = "Your mom %s %s." % (
        input.groups()[0],
        input.groups()[1],
    )
    if len(msg.split(" ")) > 20:
        return
    if random.choice(range(50)) == 0:
        phenny.say(msg)
your_mom.rule = r"^.* (is|has|used to be) (.+)\W?$"
your_mom.priority = 'medium'


@smart_ignore
def op_giver(phenny, input):
    target = input.groups()[1]
    if input.owner:
        phenny.write(['MODE', "##brittslittlesliceofheaven", "+o", target])
op_giver.rule = r'^(!|\x01ACTION )op ([a-zA-Z0-9\-_]+)$'
op_giver.priority = 'medium'


@smart_ignore
def random_topic(phenny, input):
    target = input.groups()[1]

    if target.isdigit():
        quote = DBSession.query(Quote).filter(
            Quote.id == int(target)
        )
    else:
        quote = DBSession.query(Quote).join(
            Message
        ).join(User).join(Room).filter(
            Room.name == input.sender
        )
        if target:
            quote = quote.filter(Message.body.ilike("%%%s%%" % target))
    quote = quote.order_by(
        sa.func.random()
    ).first()
    if not quote:
        return
    topic = "Welcome to %s | <%s> %s" % (
        input.sender,
        quote.message.user.nick,
        quote.message.body
    )
    phenny.write(['TOPIC', input.sender], topic)
random_topic.rule = r'^(!)topic ?(.*)?$'
random_topic.priority = 'medium'


limited_channels = {
    "#reddit-stlouis": {
        "ignored": [
            grab,
            touch,
            your_mom,
            command_help,
            fetch_quote,
            random_user_quote,
            random_quote,
            trending,
        ],
        "allowed": [],
    },
    "#r/kansascity": {
        "ignored": [
            touch,
        ]
    },
}
