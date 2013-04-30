#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json

__author__ = "Régis Décamps"
import webapp2
import csv
from model import Film, Rating
import urllib


from google.appengine.api import urlfetch

EXPECTED_FIRST_LINE = '"position","const","created","modified","description","Title","Title type","Directors","You rated","IMDb Rating","Runtime (mins)","Year","Genres","Num. Votes","Release Date (month/day/year)","URL"'


class ImdbImporter(webapp2.RequestHandler):
    def post(self):
        csv = ImdbCsvReader(self.request.POST.multi['rating_history'].file)
        o = self.response.out
        o.write('<p>Importing&hellip;</p><ul>')
        for rating in csv:
            o.write('<li><a href="{url}">{title}</a> {note}/10</li>'.format(title=rating.film.title, note=rating.score,
                                                                        url=rating.film.id))
            fb_post_rating(rating, self.request.get('access_token'))
        o.write('</ul>')
        o.write('This ratings will appear shortly on your Facebook timeline')


def fb_find_film(rating):
    ''' replace the film ID by the first result of fb search on the tiltle '''
    fields = {'q': rating.film.title, 'type': 'page'}
    data = urllib.urlencode(fields)
    result = urlfetch.fetch(url='http://graph.facebook.com/search?'+data)
    if result.status_code == 200:
        content = json.loads(result.content)
        candidate_films = content['data']
        for page in candidate_films:
            if page['category'] == 'Movie':
                rating.film.id = page['id']
                break
    else:
        print(result.content)


def fb_post_rating(rating, access_token):
    fb_find_film(rating)

    fields = {'access_token': access_token,
              'method': 'POST',
              'rating:value': rating.score,
              'rating:scale': rating.scale,
              'rating:normalized_value': rating.normalized_rating,
              'movie': rating.film.id}
    data = urllib.urlencode(fields)
    result = urlfetch.fetch(url='https://graph.facebook.com/me/video.rates',
                            payload=data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
    return result


class ImdbCsvReader(object):
    def __init__(self, file):
        first_line = file.readline()
        if first_line.strip() != EXPECTED_FIRST_LINE:
            raise ValueError("The file must be a IMDb CSV export")
        self.csv = csv.reader(file, delimiter=',', quotechar='"')

    def __iter__(self):
        return self

    def next(self):
        data = self.csv.next()
        film = Film(data[5], data[15])
        rating = Rating(film, data[8])
        return rating


if __name__ == '__main__':
    from google.appengine.api import apiproxy_stub_map, urlfetch_stub

    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
    urlfetch_stub.URLFetchServiceStub())
    with open('test/film rating history.csv', 'r') as file:
        csv = ImdbCsvReader(file)
        for rating in csv:
            fb_find_film(rating)
            print('{rating} {url}'.format(rating=rating, url=rating.film.id))
