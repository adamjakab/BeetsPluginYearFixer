#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/27/20, 3:52 PM
#  License: See LICENSE.txt
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/27/20, 9:48 AM
#  License: See LICENSE.txt

import logging
import sys

__logger__ = logging.getLogger('beets.yearfixer')

from urllib.parse import quote_plus

from beets.library import Item

MB_BASE = "https://musicbrainz.org/ws/2/"


def say(msg, log_only=True, is_error=False):
    """Log and write to stdout
    """
    _level = logging.DEBUG
    _level = _level if log_only else logging.INFO
    _level = _level if not is_error else logging.ERROR

    __logger__.log(level=_level, msg=msg)


def get_mb_search_url(item: Item):
    mb_artistid = item.get("mb_artistid")
    title = item.get("title")

    if not mb_artistid or not title:
        raise AttributeError("Missing tag(mb_artistid or title)! Cannot build MB url.")

    query = 'arid:{arid} AND recording:"{title}"'.format(arid=mb_artistid, title=title)
    url = "{base}recording/?query={qry}&fmt={fmt}".format(base=MB_BASE, qry=query, fmt="json")

    return quote_plus(url, safe=':/&?=')


def extract_original_year_from_mb_data(data):
    answer = None

    if "recordings" in data.keys():
        for recording in data["recordings"]:
            if "releases" in recording.keys():
                for release in recording["releases"]:
                    if "date" in release.keys():
                        try:
                            # date should be formatted: yyyy-mm-dd (mm and dd might be missing)
                            rel_year = int(release["date"][:4])
                        except ValueError:
                            continue
                        except AttributeError:
                            continue
                        answer = rel_year if not answer or rel_year < answer else answer

    return answer
