import requests
from typing import Dict, List
from urllib.parse import urlencode


def search(keyword: str) -> List[Dict]:
    search_response = _get_search_results(keyword)
    results = _parse_search_results(search_response)
    return results


def _search_url(keyword: str) -> str:
    q = urlencode({
        'app_id': 'areena_web_personal_prod',
        'app_key': '6c64d890124735033c50099ca25dd2fe',
        'client': 'yle-areena-web',
        'language': 'fi',
        'v': 9,
        'episodes': 'true',
        'packages': 'true',
        'query': keyword,
        'service': 'tv',
        'offset': 0,
        'limit': 7,
    })
    return f'https://areena.api.yle.fi/v1/ui/search?{q}'


def _get_search_results(keyword: str) -> Dict:
    params = {
        'app_id': 'areena_web_personal_prod',
        'app_key': '6c64d890124735033c50099ca25dd2fe',
        'client': 'yle-areena-web',
        'language': 'fi',
        'v': 9,
        'episodes': 'true',
        'packages': 'true',
        'query': keyword,
        'service': 'tv',
        'offset': 0,
        'limit': 7,
    }
    r = requests.get('https://areena.api.yle.fi/v1/ui/search', params=params)
    r.raise_for_status()
    return r.json()


def _parse_search_results(search_response: Dict) -> List[Dict]:
    image_url = 'https://images.cdn.yle.fi/image/upload/ar_1.0,c_fill,d_yle-areena.jpg,dpr_auto,f_auto,fl_lossy,q_auto:eco,w_65/v1644410176/{}.jpg'

    results = []
    for item in search_response.get('data', []):
        uri = item.get('pointer', {}).get('uri')
        pointer_type = item.get('pointer', {}).get('type')

        if item.get('type') == 'card' and uri:
            # TODO: series
            if pointer_type in ['episode', 'clip']:
                title = item.get('title', '???')
                image_id = item.get('image', {}).get('id')

                results.append({
                    'homepage': uri,
                    'title': title,
                    'thumbnail_image_url': image_url.format(image_id),
                })

    return results


if __name__ == '__main__':
    print(search('Pasila'))
