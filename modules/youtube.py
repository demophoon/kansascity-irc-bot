import urllib
import json
import re

get_data_url = "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json"

def smart_ignore(fn):
    def callable(phenny, input):
        if check_ignore(phenny, input):
            return None
        if input.sender in limited_channels:
            if fn in [x._original for x in limited_channels[input.sender]['ignored']]:
                return None
        return fn(phenny, input)
    callable._original = fn
    return callable


def check_ignore(phenny, input):
    ignored_nicks = [
        ".*bot",
    ]
    nick = input.nick
    if not input.sender.startswith("#"):
        return True
    for ignored_nick in ignored_nicks:
        if re.search(re.compile(ignored_nick, re.IGNORECASE), nick):
            return True

def get_duration(seconds):
    if seconds < 60:
        return ":%s" % "{0:02d}".format(seconds)
    elif seconds > 61 and seconds < 3600:
        return "%d%s" % (seconds / 60, get_duration(seconds % 60))
    elif seconds > 3601:
        return "%d:%s" % (seconds / 3600, get_duration(seconds % 3600))


def get_video_information(videoid):
    yturl = get_data_url % (videoid)
    try:
        vid = json.loads(urllib.urlopen(yturl).read())
        vid_obj = {
            'title': vid['entry']['title']['$t'],
            'duration': get_duration(vid['entry']['media$group']['media$content'][0]['duration']),
            'description': vid['entry']['media$group']['media$description']['$t'],
            'author': vid['entry']['author'][0]['name']['$t'],
            'shorturl': "http://youtu.be/" + videoid,
        }
        return vid_obj
    except Exception as e:
        print e
        return False


@smart_ignore
def yt_context(phenny, input):
    matches = re.match(yt_context.rule, input.group())
    target = matches.groups()[0]
    yt = get_video_information(target)
    if yt:
        phenny.say("YouTube: \"%s\" (%s) by %s - %s" % (
            yt['title'],
            yt['duration'],
            yt['author'],
            yt['shorturl'],
        ))

# https://www.youtube.com/watch?v=ygr5AHufBN4
# https://youtu.be/ygr5AHufBN4

yt_context.rule = r'.*https?://.*?youtu[a-zA-Z\./=\?]*([a-zA-Z0-9_-]{11})(&list=)?'
yt_context.priority = 'medium'

limited_channels = {
    "#reddit-stlouis": {
        "ignored": [
            yt_context
        ]
    },
}
