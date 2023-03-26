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
    query_payload = {
        "queries": query,
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
    for i in range(10):
        sleep(2)
        res = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": token},
        )
        res.raise_for_status()
        if res.json()['data']['status'] == 'SUCCEEDED':
            break
    else:
        raise SearchError("Actor run didn't complete after 5 tries")

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

    results = search_query(sys.argv[1], token)

    from pprint import pprint
    pprint(results)
