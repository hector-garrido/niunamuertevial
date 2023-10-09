# Automatiza la búsqueda de resultados
from typing import List, Optional
from time import sleep
from dataclasses import dataclass
import sys
import os

import requests


class SearchError(Exception):
    pass


@dataclass
class SearchResult:
    url: str
    date: Optional[str]
    keywords: List[str]


def search_query(query: str, token: str) -> List[SearchResult]:
    try:
        return _search_query(query, token)
    except requests.HTTPError:
        raise SearchError('HTTPError while making request')


def _search_query(query: str, token: str) -> List[str]:
    ''' Dada una consulta devuelve una lista con URLS obtenidas a partir de la
    búsqueda en google con los resultados. '''
    # create a task that will search the results
    # to tune this request see: https://apify.com/apify/google-search-scraper/input-schema#resultsPerPage
    query_payload = {
        "queries": query,
        "resultsPerPage": 100,
        "countryCode": "mx",
    }
    res = requests.post(
        f"https://api.apify.com/v2/acts/apify~google-search-scraper/runs",
        params={"token": token},
        json=query_payload,
    )
    res.raise_for_status()

    run = res.json()['data']
    run_id = run['id']
    dataset_id = run['defaultDatasetId']

    # query for the state of the dataset and wait until it is finished
    N_TRIES = 2
    for i in range(N_TRIES):
        sleep(2)
        res = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": token},
        )
        sleep(60)
        res.raise_for_status()
        sleep(60)
        if res.json()['data']['status'] == 'SUCCEEDED':
            break
    else:
        raise SearchError(f"Actor run didn't complete after {N_TRIES} tries")

    res = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        params={"token": token},
    )
    res.raise_for_status()

    return list(map(
        lambda r: SearchResult(
            r['url'],
            r.get('date'),
            r['emphasizedKeywords'],
        ),
        res.json()[0]['organicResults']
    ))


if __name__ == '__main__':
    token = os.getenv('APIFY_TOKEN')

    if token is None:
        print("Por favor establece la variable de entorno APIFY_TOKEN y ejecuta de nuevo el comando")
        exit(1)

    try:
        query = sys.argv[1]
        print(f'Using provided query: {query}')
    except IndexError:
        query = '(atropella OR atropellada OR atropellados OR atropelladas OR atropellado OR arrollado OR arrollada OR arrolla OR embiste) AND (muerte OR muerto OR muerta OR muere OR murió OR fallecido OR fallecida OR fallece OR falleció OR perece OR pereció OR cuerpo OR cadáver OR fatal OR mortal OR mata) -site:sv -site:es -site:cl -site:pe -site:ar -site:co -site:hn'
        print(f'Using default query: {query}')

    results = search_query(query, token)

    from pprint import pprint
    pprint(results)
