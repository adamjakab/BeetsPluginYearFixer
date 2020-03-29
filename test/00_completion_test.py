#  Copyright: Copyright (c) 2020., Adam Jakab
#
#  Author: Adam Jakab <adam at jakab dot pro>
#  Created: 2/19/20, 12:31 PM
#  License: See LICENSE.txt

from test.helper import TestHelper, Assertions, \
    PLUGIN_NAME, PLUGIN_SHORT_DESCRIPTION, PACKAGE_NAME, PACKAGE_TITLE, PLUGIN_VERSION, \
    capture_log

plg_log_ns = 'beets.{}'.format(PLUGIN_NAME)


class CompletionTest(TestHelper, Assertions):
    """Test invocation of the plugin.
    """

    def test_application(self):
        output = self.runcli()
        self.assertIn(PLUGIN_NAME, output)
        self.assertIn(PLUGIN_SHORT_DESCRIPTION, output)

    def test_application_plugin_list(self):
        output = self.runcli("version")
        self.assertIn("plugins: {0}".format(PLUGIN_NAME), output)

    def test_run_plugin(self):
        with capture_log(plg_log_ns) as logs:
            self.runcli(PLUGIN_NAME)
        self.assertIn("Your query did not produce any results.", "\n".join(logs))

    def test_plugin_version(self):
        with capture_log(plg_log_ns) as logs:
            self.runcli(PLUGIN_NAME, "--version")

        versioninfo = "{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=PACKAGE_TITLE,
            pn=PACKAGE_NAME,
            ver=PLUGIN_VERSION
        )
        self.assertIn(versioninfo, "\n".join(logs))
