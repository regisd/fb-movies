#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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
                                                                            url=rating.film.url))
            fb_post_rating(rating, self.request.get('access_token'))
        o.write('</ul>')
        o.write('This ratings will appear shortly on your Facebook timeline')


def fb_post_rating(rating, access_token):


    fields = {'access_token': access_token,
              'method': 'POST',
              'rating:value': rating.score,
              'rating:scale': rating.scale,
              'rating:normalized_value': rating.normalized_rating,
              'movie': rating.film.url}
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
    with open('test/film rating history.csv', 'r') as file:
        csv = ImdbCsvReader(file)
        for rating in csv:
            print('{rating} {url}'.format(rating=rating, url=rating.film.url))
