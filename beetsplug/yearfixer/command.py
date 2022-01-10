#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 3/27/20, 3:52 PM
#  License: See LICENSE.txt

import time
from optparse import OptionParser

import requests
from beets.dbcore.query import NumericQuery, MatchQuery, AndQuery, OrQuery, \
    NoneQuery
from beets.library import Library, Item, parse_query_parts
from beets.ui import Subcommand, decargs
from confuse import Subview
from beetsplug.yearfixer import common


class YearFixerCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    cfg_force = False

    def __init__(self, cfg):
        self.config = cfg

        self.parser = OptionParser(usage='beet {plg} [options] [QUERY...]'.format(
            plg=common.plg_ns['__PLUGIN_NAME__']
        ))

        self.parser.add_option(
            '-f', '--force',
            action='store_true', dest='force', default=self.cfg_force,
            help=u'[default: {}] force analysis of items with non-zero bpm '
                 u'values'.format(
                self.cfg_force)
        )

        self.parser.add_option(
            '-v', '--version',
            action='store_true', dest='version', default=False,
            help=u'show plugin version'
        )

        # Keep this at the end
        super(YearFixerCommand, self).__init__(
            parser=self.parser,
            name=common.plg_ns['__PLUGIN_NAME__'],
            aliases=[common.plg_ns['__PLUGIN_ALIAS__']] if common.plg_ns['__PLUGIN_ALIAS__'] else [],
            help=common.plg_ns['__PLUGIN_SHORT_DESCRIPTION__']
        )

    def func(self, lib: Library, options, arguments):
        self.lib = lib
        self.query = decargs(arguments)
        self.cfg_force = options.force

        if options.version:
            self.show_version_information()
            return

        self.handle_main_task()

    def handle_main_task(self):
        items = self.retrieve_library_items()
        if not items:
            self._say("Your query did not produce any results.", log_only=False)
            return

        for item in items:
            self.process_item(item)
            item.try_write()
            item.store()

    def process_item(self, item: Item):
        self._say("Fixing item: {}".format(item), log_only=True)

        year = item.get("year")
        original_year = item.get("original_year")

        if not original_year or self.cfg_force:
            mbdata = self._get_mb_data(item)
            if mbdata:
                extracted = common.extract_original_year_from_mb_data(mbdata)
                if extracted:
                    original_year = extracted
                    self._say("Got (MusicBrainz) recording `original_year`: {}"
                              .format(original_year))

            if not original_year:
                original_year = self.get_mean_value_for_album(item, "original_year")
                self._say("Got (mean-album) `original_year`: {}".format(original_year))

            if not original_year:
                original_year = self.get_mean_value_for_artist(item, "original_year")
                self._say("Got (mean-artist) `original_year`: {}".format(original_year))

        if not year or self.cfg_force:
            year = self.get_mean_value_for_album(item, "year")
            self._say("Got (mean-album) `year`: {}".format(year))

            if not year:
                year = self.get_mean_value_for_artist(item, "year")
                self._say("Got (mean-artist) `year`: {}".format(year))

        if original_year:
            setattr(item, "original_year", original_year)

        if year:
            setattr(item, "year", year)

        if original_year and not year:
            setattr(item, "year", original_year)

        if year and not original_year:
            setattr(item, "original_year", year)

        if not year and not original_year:
            self._say("Cannot find info!")

    def get_mean_value_for_album(self, item: Item, field_name):
        answer = None

        query = MatchQuery('mb_albumid', item.get("mb_albumid"))
        items = self.lib.items(query)
        values = []
        for it in items:
            if it.get(field_name):
                val = int(it.get(field_name))
                if 0 < val < 2100:
                    values.append(val)

        if values:
            answer = int(round(sum(values) / len(values)))

        return answer

    def get_mean_value_for_artist(self, item: Item, field_name):
        answer = None

        query = MatchQuery('mb_artistid', item.get("mb_artistid"))
        items = self.lib.items(query)
        values = []
        for it in items:
            if it.get(field_name):
                val = int(it.get(field_name))
                if 0 < val < 2100:
                    values.append(val)

        if values:
            answer = int(round(sum(values) / len(values)))

        return answer

    def _get_mb_data(self, item: Item):
        data = {}

        try:
            url = common.get_mb_search_url(item)
        except AttributeError as err:
            self._say(err, is_error=True)
            return data

        # self._say(u'fetching URL: {}'.format(url))

        headers = {
            'User-Agent': '{pt}/{ver} ( {url} )'.format(
                pt=common.plg_ns['__PACKAGE_TITLE__'],
                ver=common.plg_ns['__version__'],
                url=common.plg_ns['__PACKAGE_URL__'],
            ),
        }

        max_retries = 5
        sleep_time = 3
        retries = 0

        while not data:
            retries += 1
            # self._say('Retry #{}'.format(retries))
            if retries > max_retries:
                self._say("Maximum({}) retries reached. Abandoning.".format(max_retries), is_error=True)
                break

            try:
                res = requests.get(url, headers=headers)
            except requests.RequestException as err:
                self._say(err, is_error=True)
                break

            if res.status_code == 503:
                # we hit the query limit -
                # https://musicbrainz.org/doc/XML_Web_Service/Rate_Limiting
                self._say('Retry #{} - Query LIMIT Hit! sleeping {}s.'
                          .format(retries, sleep_time))
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

        if self.cfg_force:
            full_query = parsed_cmd_query
        else:
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
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
