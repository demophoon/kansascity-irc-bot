import json

import pylast


f = open('./modules/lastfm.json', 'r')
secret = json.loads(f.read())
print secret

network = pylast.LastFMNetwork(
    api_key=secret['api_key'],
    api_secret=secret['secret'],
    username=secret['username'],
    password_hash=pylast.md5(secret['password']),
)


def format_track(song_obj):
    track = song_obj.track.title
    artist = song_obj.track.artist.name
    # album = song_obj.album
    return "%s by %s" % (track, artist)


def current_song(phenny, input):
    username = input.groups()[1].strip()
    if not username:
        username = secret['username']
    user = network.get_user(username)
    recent_tracks = user.get_recent_tracks()
    tracks = ", ".join([format_track(x) for x in recent_tracks[:3]])
    phenny.say("%s recent tracks: %s" % (username, tracks))
current_song.rule = r'^!(nowplaying|currentsong|playing|song|track|last\.?fm)(.*)$'
current_song.priority = 'medium'
