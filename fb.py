#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"
import json
import logging
import urllib

from google.appengine.api import urlfetch

# https://developers.facebook.com/docs/opengraph/howtos/publishing-with-app-token/
APP_ACCESS_TOKEN = "608738222470406|EcMxWzL92NhXoj1joBtEQfaAYpc"


def get_user(token):
    '''
    GET /debug_token?
     input_token={input-token}&
     access_token={access-token}
    '''
    fields = {'input_token': token, 'access_token': APP_ACCESS_TOKEN}
    data = urlencode_utf8(fields)

    result = urlfetch.fetch(url='https://graph.facebook.com/debug_token?' + data)
    if result.status_code == 200:
        content = json.loads(result.content)
        token_info = content['data']
        return token_info['user_id']
    else:
        logging.error(result.content)
        return None


def find_film(film):
    ''' replace the film ID by the first result of fb search on the title '''
    fields = {'q': film.title + ' ' + film.director, 'type': 'page'}
    data = urlencode_utf8(fields)
    result = urlfetch.fetch(url='http://graph.facebook.com/search?' + data)
    if result.status_code == 200:
        content = json.loads(result.content)
        candidate_films = content['data']
        for page in candidate_films:
            if page['category'] == 'Movie':
                film.fb_id = int(page['id'])
                break
    else:
        logging.error(result.content)


def post_rating(rating, access_token):
    fields = {'access_token': access_token,
              'method': 'POST',
              'rating:value': rating.score,
              'rating:scale': rating.scale,
              'rating:normalized_value': rating.normalized_rating,
              'movie': rating.film.fb_id if rating.film.fb_id else rating.film.imdb_url}
    data = urlencode_utf8(fields)
    result = urlfetch.fetch(url='https://graph.facebook.com/me/video.rates',
                            payload=data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
    logging.debug("Result {status} for {data}".format(status=result.status_code, data=fields))
    return result


from urllib import quote_plus


def urlencode_utf8(params):
    '''
    Python27 urllib doesn't support unicode
    '''
    encoded_dict = dict((k, v.encode('UTF-8')) for k, v in params.items() if isinstance(v, basestring))
    return urllib.urlencode(encoded_dict)