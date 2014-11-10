#!/usr/bin/env python
# encoding: utf-8

import random
import re
import itertools

import sqlalchemy as sa
import nltk
from nltk.corpus import wordnet as wn

from modules.quote import DBSession, Message, User, Room

tokenizer = nltk.tokenize.RegexpTokenizer("[\w'-]+")
#tagger = nltk.UnigramTagger(nltk.corpus.brown.tagged_sents())


def get_synonyms(word):
    if len(word) > 1:
        similar_words = [x.similar_tos() for x in wn.synsets(word)]
        similar_words = [item.lemma_names for l in similar_words for item in l]
        suggestions = [word for l in similar_words for word in l]
        return suggestions
    return [word]


def action(msg):
    msg = '\x01ACTION %s\x01' % msg
    return msg


def word_definer(phenny, input):
    target = input.groups()[0]
    definitions = enumerate(wn.synsets(target), start=1)
    definitions = [
        "%d (%s): %s" % (index, synset.lemma_names[0], synset.definition) for index, synset in definitions
    ]
    phenny.say(". ".join(definitions))
word_definer.rule = r"^!define (\w+)"
word_definer.priority = "medium"


def syn_func(msg):
    words = tokenizer.tokenize(msg)
    for word in words:
        suggestions = get_synonyms(word)
        if word.lower() == "windows":
            suggestions.append("windurs")
        if 'cardinal' in suggestions:
            continue
        if suggestions:
            msg = msg.replace(word, random.choice(suggestions), 1)
    return msg


def synonymize(phenny, input):
    target = input.groups()[1].lower()
    words = tokenizer.tokenize(target)
    if len(words) == 1:
        nick = words[0]
        message = DBSession.query(Message).join(User).join(Room).filter(
            User.nick.ilike("%s%%" % target)
        ).filter(
            Room.name == input.sender
        ).filter(
            sa.not_(Message.body.like("!%"))
        ).order_by(Message.created_at.desc()).first()
        if message:
            target = message.body
    phenny.say(syn_func(target))
synonymize.rule = r"^!(synonymize|syn|rejigro) (.+)"
synonymize.priority = "medium"


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
define.rule = r"$nickname\W? (what|when|where|why|which|who|how|can|did|does|are|is) ([a-zA-Z']+) ([a-zA-Z0-9 \-,'\"]+)\??"
define.priority = "medium"

james_sayings = [
    "%(nick)s, my love for you burns hot like the flames of those produced by %(number)d suns.",
    "%(nick)s, my love for you burns like the flames of hell as they are infinite and eternal.",
    "%(nick)s, the eternal happiness that I achieve when you message me cannot be calculated by any super computer known to man.",
    "%(nick)s, If my love for you was to be expressed as a span of time it would be greater than %(number)d of years.",
    "%(nick)s, I will follow you to the ends of the earth if it meant I could spend even one more moment with you.",
    "%(nick)s, Your beauty rivals that of Aphrodite's.",
    "%(nick)s, Your shine to your radiating smile is equivalent to that of a thousand exploding stars.",
    "%(nick)s, Your gentle gaze can put a thousand warring men to sleep.",
    "%(nick)s, Like a well made sword, your beauty can pierce even the toughest of hearts.",
    "%(nick)s, If I could put a time limit on the love in which I have for you it would be 10,000 years, for it would not only last this lifetime, but for many more lifetimes after.",
]


def james_me(phenny, input):
    facts = {
        'nick': input.groups()[1].strip(),
        'number': random.randint(1000, 10000000),
    }
    if facts['nick'].lower() == 'me':
        facts['nick'] = input.nick
    elif facts['nick'].lower() == 'demophoon':
        phenny.say("no, thats weird.")
        return
    saying = random.choice(james_sayings)
    saying = saying % facts
    if random.choice(range(2)) == 1:
        saying = syn_func(saying)
    if input.groups()[0] == 'JAMES':
        saying = saying.upper()
    phenny.say(saying)
james_me.rule = "^(james|JAMES|!hiton) (.*)"
james_me.priority = 'medium'
