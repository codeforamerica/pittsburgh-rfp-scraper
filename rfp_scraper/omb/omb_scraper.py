#! /usr/bin/env python

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from rfp_scraper.scraper import RfpScraper

class OmbScraper(RfpScraper):
    def __init__(self, base_url=None):
        self.base_url = 'http://pittsburghpa.gov/omb/contract-bids' if not base_url else base_url
        self.scraped = False

    def process_bid_text(self, elem):
        '''
        Extracts names, resources, and other text from elements
        '''

        bid = {}

        if isinstance(elem, NavigableString):
            if elem != '\n':
                bid['text_description'] = elem.replace('\r', '').replace('\n', '').replace(u'\xa0', '')
        elif elem.name == 'a':
            bid['name'] = elem.text
            bid['resource'] = elem.attrs.get('href')
        elif elem.name in ['div', 'p', 'span']:
            if elem.a:
                bid['additional_information'] = self.process_bid_text(elem.a)
            else:
                bid['text_description'] = elem.text.replace('\r', '').replace('\n', '').replace(u'\xa0', '')

        return bid

    def process_ul_children(self, ul):
        '''
        Takes in a beautiful soup elem and recursively
        processes its children. Takes in a parent element
        as an argument and returns a dictionary of text
        and links
        '''
        output = []

        for li in ul.find_all('li', recursive=False):
            for child in li.contents:
                if child.name == 'ul':
                    output.append(self.process_ul_children(child))
                else:
                    bid_text = process_bid_text(child)
                    if len(bid_text.keys()) > 0:
                        output.append(bid_text)

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
                current_header = current_elem.text.replace(u'\xa0', '')

            elif current_elem.name != 'ul':
                continue

            elif current_elem.name == 'ul':
                page_contents = self.process_ul_children(current_elem)

            if current_header and page_contents:
                output_bids.append({
                    'bid_type': current_header,
                    'open_bids': page_contents
                })

                page_contents = None

        self.scraped = True
        return output_bids


    def rfp_parser(self, bids):
        metadata, information = [], []
        for bid in bids.get('open_bids'):
            if isinstance(bid, dict):
                metadata.append(bid.get('additional_information', bid))
            elif isinstance(bid, list):
                information.append([
                    i.get('additional_information', i) for i in bid
                ])
        zipped = zip(metadata, information)
        for i in zipped:
            i[0]['additional_information'] = i[1]
        return [i[0] for i in zipped]

    def construction_ela_parser(self, bids):
        metadata, information = [], []
        for bid in bids.get('open_bids'):
            if sorted(bid.keys()) == ['name', 'resource']:
                metadata.append(bid)
            else:
                information.append(bid)
        zipped = zip(metadata, information)
        for i in zipped:
            i[0]['additional_information'] = i[1]
        return [i[0] for i in zipped]    

    def rfq_and_letter_parser(self, bids):
        metadata, information = [], []
        for bid in bids.get('open_bids'):
            if isinstance(bid, dict):
                metadata.append(bid)
            elif isinstance(bid, list):
                information.append(bid)
        zipped = zip(metadata, information)
        for i in zipped:
            i[0]['additional_information'] = i[1]
        return [i[0] for i in zipped]

    def format_bids(self, bids):
        if not self.scraped:
            raise Exception('This data is stale and will format incorrectly. Please re-scrape.')

        formatted = []
        for bid in bids:
            if bid.get('bid_type') == 'REQUESTS FOR PROPOSALS:':
                test_bid = self.rfp_parser(bid)
            elif bid.get('bid_type') in ['CONSTRUCTION PROJECTS:', 'EQUIPMENT LEASING AUTHORITY BIDS:'] :
                test_bid = self.construction_ela_parser(bid)
            elif bid.get('bid_type') == 'REQUESTS FOR QUOTE & LETTER OF INTENT:':
                test_bid = self.rfq_and_letter_parser(bid)
            else:
                test_bid = bid.get('open_bids')
            formatted.append({
                'bid_type': bid.get('bid_type'),
                'open_bids': test_bid
            })
        self.scraped = False
        return formatted