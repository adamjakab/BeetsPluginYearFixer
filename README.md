[![Coverage Status](https://coveralls.io/repos/github/adamjakab/BeetsPluginYearFixer/badge.svg?branch=master)](https://coveralls.io/github/adamjakab/BeetsPluginYearFixer?branch=master)
[![PyPi](https://img.shields.io/pypi/v/beets-yearfixer.svg)](https://pypi.org/project/beets-yearfixer/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/beets-yearfixer.svg)](https://pypi.org/project/beets-yearfixer/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.txt)

# YearFixer (Beets Plugin)

The *beets-yearfixer* plugin finds the `original_year` for each of your songs by querying the MusicBrainz database and finding the first release date that is associated with it. If the MB database query is unsuccessful, it will then use the other songs in the same album as reference and calculate the mean `original_year` between them. If this does not yield any results then the same will be done for all songs of the artist. For the `year` attribute the same procedure will be used except that the MB database is not queried. 


## Installation
The plugin can be installed via:


    $pip install beets-yearfixer


Activate the plugin in your configuration file by adding `yearfixer` to the plugins section:

```yaml
plugins:
    - yearfixer
```

## Usage

Invoke the plugin as:

    $ beet yearfixer [options] [QUERY...]


The following command line options are available:

**--force [-f]**: Force setting the values on items even if the value has been previously set.

**--version [-v]**: Display the version number of the plugin. Useful when you need to report some issue and you have to state the version of the plugin you are using.


## Configuration
The `force` options can also be set through the configuration like this: 

```yaml
force: yes
```


## Issues
- If something is not working as expected please use the Issue tracker.
- If the documentation is not clear please use the Issue tracker.
- If you have a feature request please use the Issue tracker.
- In any other situation please use the Issue tracker.


## Other plugins by the same author

- [beets-goingrunning](https://github.com/adamjakab/BeetsPluginGoingRunning)
- [beets-xtractor](https://github.com/adamjakab/BeetsPluginXtractor)
- [beets-yearfixer](https://github.com/adamjakab/BeetsPluginYearFixer)
- [beets-autofix](https://github.com/adamjakab/BeetsPluginAutofix)
- [beets-describe](https://github.com/adamjakab/BeetsPluginDescribe)
- [beets-bpmanalyser](https://github.com/adamjakab/BeetsPluginBpmAnalyser)
- [beets-template](https://github.com/adamjakab/BeetsPluginTemplate)


## Final Remarks
Enjoy!
