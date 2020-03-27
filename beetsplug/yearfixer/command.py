#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/27/20, 3:52 PM
#  License: See LICENSE.txt

import time
from optparse import OptionParser

import requests
from beets.dbcore.query import NumericQuery, MatchQuery, AndQuery, OrQuery, NoneQuery
from beets.library import Library, Item, parse_query_parts
from beets.ui import Subcommand, decargs
from beets.util.confit import Subview

from beetsplug.yearfixer import common

# The plugin
__PLUGIN_NAME__ = u'yearfixer'
__PLUGIN_SHORT_DESCRIPTION__ = u'Fix original_year and year tags'


class YearFixerCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    def __init__(self, cfg):
        self.config = cfg

        self.parser = OptionParser(usage='beet yearfixer [options] [QUERY...]')

        self.parser.add_option(
            '-v', '--version',
            action='store_true', dest='version', default=False,
            help=u'show plugin version'
        )

        # Keep this at the end
        super(YearFixerCommand, self).__init__(
            parser=self.parser,
            name=__PLUGIN_NAME__,
            help=__PLUGIN_SHORT_DESCRIPTION__
        )

    def func(self, lib: Library, options, arguments):
        self.lib = lib
        self.query = decargs(arguments)

        if options.version:
            self.show_version_information()
            return

        self.handle_main_task()

    def handle_main_task(self):
        items = self.retrieve_library_items()
        for item in items:
            self.process_item(item)
            item.try_write()
            item.store()

    def process_item(self, item: Item):
        self._say("Finding year for: {}".format(item), log_only=False)

        year = item.get("year")
        original_year = item.get("original_year")

        if not original_year:
            mbdata = self._get_mb_data(item)
            if mbdata:
                original_year = common.extract_original_year_from_mb_data(mbdata)
                self._say("Got original year: {}".format(original_year), log_only=False)
                setattr(item, "original_year", original_year)

        if original_year and not year:
            setattr(item, "year", original_year)

        if year and not original_year:
            setattr(item, "original_year", year)

        if not year and not original_year:
            self._say("Cannot find year info")

    def _get_mb_data(self, item: Item):
        data = {}

        try:
            url = common.get_mb_search_url(item)
        except AttributeError as err:
            self._say(err, is_error=True)
            return data

        self._say(u'fetching URL: {}'.format(url))

        # todo: use about.py for values
        headers = {
            'User-Agent': 'BeetsPluginYearFixer/0.0.1 ( https://github.com/adamjakab/BeetsPluginYearFixer )',
        }

        max_retries = 5
        sleep_time = 3
        retries = 0

        while not data:
            retries += 1
            self._say('Retry #{}'.format(retries))
            if retries > max_retries:
                self._say("Maximum({}) retries reached. Abandoning.".format(max_retries), is_error=True)
                break

            try:
                res = requests.get(url, headers=headers)
            except requests.RequestException as err:
                self._say(err, is_error=True)
                break

            if res.status_code == 503:
                # we hit the query limit - https://musicbrainz.org/doc/XML_Web_Service/Rate_Limiting
                self._say('Query LIMIT Hit!')
                time.sleep(sleep_time)
                continue

            if res.status_code == 404:
                self._say('404 - Not found.', is_error=True)
                break

            try:
                data = res.json()
            except ValueError as err:
                self._say('Invalid Response: {}'.format(err), is_error=True)
                break

        return data

    def retrieve_library_items(self):
        cmd_query = self.query
        parsed_cmd_query, parsed_ordering = parse_query_parts(cmd_query, Item)

        parsed_plg_query = OrQuery([
            NumericQuery('year', '0'),
            MatchQuery('year', ''),
            NoneQuery('year'),
            NumericQuery('original_year', '0'),
            MatchQuery('original_year', ''),
            NoneQuery('original_year'),
        ])

        full_query = AndQuery([parsed_cmd_query, parsed_plg_query])
        self._say("Selection query: {}".format(full_query))

        return self.lib.items(full_query, parsed_ordering)

    def show_version_information(self):
        from beetsplug.yearfixer.version import __version__
        self._say("Plot(beets-{}) plugin for Beets: v{}".format(__PLUGIN_NAME__, __version__))

    def _say(self, msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
