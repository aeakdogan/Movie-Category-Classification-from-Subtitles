from collections import namedtuple
from itertools import groupby


def parse_subtitle(filename):
    # "chunk" our input file, delimited by blank lines
    with open(filename, 'rb') as f:
        res = [list(g) for b,g in groupby(f, lambda x: bool(x.strip())) if b]

    Subtitle = namedtuple('Subtitle', 'number start end content at_minute at_seconds')

    subs = []

    for sub in res:
        if len(sub) >= 3: # not strictly necessary, but better safe than sorry
            sub = [x.strip() for x in sub]

            number = sub[0].decode("UTF-8")
            start_end = sub[1].decode("UTF-8")
            content = sub[2]


            start, end = start_end.split(' --> ') # e.g. 02:14:53,085
            at_minute = int(start[:2]) * 60 + int(start[3:5])
            at_seconds = int(start[:2]) * 3600 + int(start[3:5]) * 60 + int(start[6:8])
            subs.append(Subtitle(number, start, end, content, at_minute, at_seconds))

    return subs

# subs = parse_subtitle("castaway.srt")