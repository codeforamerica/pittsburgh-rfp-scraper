#! /usr/bin/env python

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from rfp_scraper.scraper import RfpScraper

class OmbScraper(RfpScraper):
    def __init__(self, base_url=None):
        self.base_url = 'http://pittsburghpa.gov/omb/contract-bids' if not base_url else base_url

    def process_ul_children(self, bs_elem):
        '''
        Takes in a beautiful soup elem and recursively
        processes its children. Takes in a parent element
        as an argument and returns a dictionary of text
        and links
        '''
        output = {}

        for elem in bs_elem.children:
            if elem.name == 'a':
                output['name'] = elem.text
                output['resource'] = elem.attrs.get('href')
            elif elem.name in ['div', 'p']:
                if elem.children:
                    output = self.process_ul_children(elem)
                else:
                    output['text_description'] = elem.text.replace('\r', '').replace('\n', '')
            elif elem.name in ['ul', 'li']:
                try:
                    output['additional_information'].append(self.process_ul_children(elem))
                except:
                    output['additional_information'] = [self.process_ul_children(elem)]
            elif isinstance(elem, NavigableString):
                if elem not in ['\n', '<br>']:
                    output['text_description'] = elem.replace('\r', '').replace('\n', '')

        return output

    def scrape(self):
        output_bids = []
        current_header, page_contents = None, None

        soup = BeautifulSoup(requests.get(self.base_url).text)

        # Bids themselves are stored in a div with class .ckBlock
        bids_div = soup.find('div', class_='ckBlock')

        # find all the first tags that are essentially section headers
        current_elem = bids_div.h4

        while current_elem.next_sibling:

            current_elem = current_elem.next_sibling

            # all the actual bids are stored in ul tags
            if current_elem.name == 'h4':
                current_header = current_elem.text

            elif current_elem.name != 'ul':
                continue

            elif current_elem.name == 'ul':
                page_contents = self.process_ul_children(current_elem)

            if current_header and page_contents:
                output_bids.append({
                    current_header: page_contents
                })

                current_header, page_contents = None, None

        return output_bids
