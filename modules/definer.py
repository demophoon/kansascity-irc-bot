#!/usr/bin/env python
# encoding: utf-8

import random
import re
import itertools

import sqlalchemy as sa

from modules.quote import DBSession, Message


def action(msg):
    msg = '\x01ACTION %s\x01' % msg
    return msg


def define(phenny, input):
    what = input.groups()[0].lower()
    is_are = input.groups()[1].lower()
    target = input.groups()[2].lower()

    allow_reverse = False

    if what == "where" and is_are == "all" and target == "the white women at":
        phenny.say(action("raises hand"))
        return
    if target.split(" ")[0] in ["you"]:
        target = target.replace(target.split(" ")[0], "i")
        is_are = "am"
    elif target.split(" ")[0] in ["your"]:
        target = target.replace(target.split(" ")[0], "my")
        #is_are = " ".join(target.split(" ")[1:])
        #target = target.split(" ")[0]
    if what.lower() == "why":
        is_are = "because"
    elif what.lower() == "where":
        is_are += " at"
    if target.split(" ")[0] in ["a", "an", "the"]:
        target = " ".join(target.split(" ")[1:])
    permutations = itertools.permutations(target.split(" "))
    definition = None
    iterations = 0
    while iterations < 5:
        iterations += 1
        try:
            search = permutations.next()
        except Exception:
            print "Error"
            break
        search = " ".join(search)
        print "Search:", search
        if allow_reverse:
            definition = DBSession.query(Message).filter(
                sa.or_(
                    Message.body.ilike("%%%s%% %s%%" % (
                        search,
                        is_are,
                    )),
                    Message.body.ilike("%% %s%%%s%%" % (
                        is_are,
                        search,
                    ))
                )
            )
        else:
            definition = DBSession.query(Message).filter(
                sa.or_(
                    Message.body.ilike("%%%s%% %s%%" % (
                        search,
                        is_are,
                    ))
                )
            )
        definition = definition.filter(sa.not_(
            Message.body.ilike("%s_%%" % phenny.nick)
        )).order_by(
            sa.func.random()
        ).first()
        if not definition:
            continue
        if not re.search(define.rule, definition.body):
            break
    if not definition:
        phenny.say(random.choice([
            "I don't know yet.",
            "I don't have the answer.",
            "You tell me.",
            "Answer unknown.",
        ]))
        return
    print definition.body
    if definition.body.lower().index(search.lower()) < \
            definition.body.lower().index(is_are.lower()):
        matches_two = re.search(
            re.compile("%s.* %s(.*)$" % (
                search,
                is_are,
            ), re.IGNORECASE),
            definition.body,
        )
        if not matches_two:
            return
        target = input.groups()[2]
        msg = "%s %s %s" % (
            search,
            is_are,
            matches_two.groups()[0],
        )
    else:
        matches_two = re.search(
            re.compile("(.*) %s.*%s" % (
                is_are,
                search,
            ), re.IGNORECASE),
            definition.body,
        )
        if not matches_two:
            return
        target = input.groups()[2]
        msg = "%s %s %s" % (
            matches_two.groups()[0],
            is_are,
            search,
        )
    phenny.say(" ".join([x.replace(" ", "") for x in msg.split(" ") if not(x.replace(" ", "") == "")]))
define.rule = r"$nickname\W? (what|when|where|why|which|who|how|can|did|does) ([a-zA-Z']+) ([a-zA-Z0-9 \-,'\"]+)\??"
define.priority = "medium"
