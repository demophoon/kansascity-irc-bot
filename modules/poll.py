rooms = {}

from collections import Counter


def start_poll(phenny, input):
    if rooms.get(input.sender):
        phenny.say("Poll already started.")
        return
    rooms[input.sender] = {
        'poll': input.groups()[0],
        'votes': [],
    }
    phenny.say("Poll has started! Vote using '!vote <answer>'")
start_poll.rule = r'^!start poll (.*)$'


def vote_poll(phenny, input):
    if not rooms.get(input.sender):
        phenny.say("No poll has been started.")
        return
    rooms[input.sender]['votes'].append(input.groups()[0].strip())
vote_poll.rule = r'^!vote (.*)$'


def end_poll(phenny, input):
    if not rooms.get(input.sender):
        phenny.say("No poll has been started.")
        return
    poll = rooms[input.sender]['poll']
    votes = rooms[input.sender]['votes']
    votes = Counter([x.lower() for x in votes])
    total_votes = sum([y[1] for y in votes.items()])
    percentage = float(votes.most_common(1)[0][1]) / float(total_votes)
    percentage *= 100
    phenny.say("The results are in! %s" % poll)
    phenny.say("The winner with %.1f%% of the vote is: %s" % (
        percentage,
        votes.most_common(1)[0][0],
    ))
    rooms[input.sender] = {}
end_poll.rule = r'^!end poll$'
