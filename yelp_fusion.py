
from __future__ import print_function
import argparse
import requests
import sys
import pickle
import pymongo
import constants
import time
import datetime

from urllib.error import HTTPError
from urllib.parse import quote

API_KEY= "joJ5oVewh2iPd_hAiQcf5A6Sv2xa_PSjGlSN_I416xS0VRe9wOcVDbdPhQGhrcwCWwIisolOp9AM9g3UQwRarcQ4Xta9Qwwx38LC_RfERO-A-uMxznm_-vXsuV9yXHYx"

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 50

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["jones2"]
mycol = mydb["vendors"]

def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(api_key, term, location, search_offset=0):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
        search_offset (int): Numer of search items to osset by
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'offset': search_offset
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(term, location, search_offset=0):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(API_KEY, term, location, search_offset)
    businesses = response.get('businesses')

    # Change 'id' key to '_id' so that it is used as mongo primary key
    for business in businesses:
        business['_id'] = business['id']
        del business['id']

    return businesses

    # if not businesses:
    #     print(u'No businesses for {0} in {1} found.'.format(term, location))
    #     return
    #
    # business_id = businesses[0]['id']
    #
    # print(u'{0} businesses found, querying business info ' \
    #     'for the top result "{1}" ...'.format(
    #         len(businesses), business_id))
    # response = get_business(API_KEY, business_id)
    #
    # print(u'Result for business "{0}" found:'.format(business_id))
    # pprint.pprint(response, indent=2)


def insert_into_DB(collection, dict_file):
    for document in dict_file:
        existing_document = collection.find_one(document)
        if not existing_document:
            document['insertion_date'] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        else:
            document = existing_document
        document['last_update_date'] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        collection.save(document)

        print(document['alias'])


def main():
    # parser = argparse.ArgumentParser()
    #
    # parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
    #                     type=str, help='Search term (default: %(default)s)')
    # parser.add_argument('-l', '--location', dest='location',
    #                     default=DEFAULT_LOCATION, type=str,
    #                     help='Search location (default: %(default)s)')
    #
    # input_values = parser.parse_args()

    # Cycle trough all cities and professions, and request search results 50
    # as a time until results exhausted

    for city in constants.us_cities:
        for profession in constants.yelp_professions:

            try:
                search_offset = 0
                while True:
                    print(city, profession, search_offset)
                    results = query_api(profession, city, search_offset)
                    # Stop if no results, or if reached 1000 limit
                    if len(results) == 0 or search_offset == 950:
                        break
                    insert_into_DB(mycol, results)
                    search_offset += 50

            except HTTPError as error:
                sys.exit(
                    'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                        error.code,
                        error.url,
                        error.read(),
                    )
                )


if __name__ == '__main__':
    main()
    #print(get_business(API_KEY, 'K6ZMvdRy_y0qfFIDj6L6qw'))


