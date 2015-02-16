#! /usr/bin/env python

class RfpScraper(object):
    def __init__(self, base_url):
        '''
        RfpScraper is the base class for scraping

        It has two methods that must be implemented: 
        scrape() and format(). More information about these
        methods can be found in their respective docstrings
        below.
        '''
        if not base_url:
            raise Exception('RfpScraper must contain a url to scrape!')

        self.base_url = base_url

    def scrape(self):
        '''
        Performs the actual scraping.

        Because individual sites may have differing requirements
        (some sites may require navigation via a system like mechanize),
        there are no implementation details listed here
        '''
        raise NotImplementedError

    def format_bids(self):
        '''
        Formats data to return in a standard format

        The preferred output is a list of dictionaries to
        allow for simple json encoding. Each dictionary must
        have the following keys, with a value of 'NULL' if
        it is not provided by the page
            []
        '''
        raise NotImplementedError