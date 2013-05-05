#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from datetime import datetime

__author__ = "Régis Décamps"
import os
import logging
import locale
import webapp2
import csv
import json
import model
import fb
from google.appengine.ext.webapp import template

EXPECTED_FIRST_LINE = '"position","const","created","modified","description","Title","Title type","Directors","You rated","IMDb Rating","Runtime (mins)","Year","Genres","Num. Votes","Release Date (month/day/year)","URL"'
IMDB_DATETIME_FMT = "%a %b %d %H:%M:%S %Y"
locale.setlocale(locale.LC_ALL, 'C')

class ImdbImporter(webapp2.RequestHandler):
    def post(self):
        rating_history_file = self.request.POST.multi['rating_history'].file
        fb_access_token = self.request.get('fb_access_token')
        fb_user_id = fb.get_user(fb_access_token)
        logging.info("Importing Ratings for {user}".format(user=fb_user_id))

        csv = ImdbCsvReader(rating_history_file)
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        imported = []

        for line in csv:
            # search film in datastore
            film = model.Film.all().filter('imdb_url =', line.url).get()
            if film is None:
                film = model.build_Film(line.title, line.director, line.runtime, line.url)
                fb.find_film(film)
                film.put()

            # find existing rating
            rating = model.Rating.all().filter('film = ', film).filter('user_id = ',fb_user_id).get()
            if not rating:
                rating = model.build_Rating(fb_user_id, film, line.score, line.created_time)
                # save in datastore
                rating.put()

            # TODO approve app so that it can watch for the user
            # fb.post_watch(rating, fb_access_token)
            response = fb.post_rating(rating, fb_access_token)

            imp = ImdbImport(rating)
            imported.append(imp)
            if response.status_code == 200:
                if not rating.film.imdb_url:
                    imp.status = 'error'
                    imp.status_msg = "Film not found on Facebook"
                else:
                    content = json.loads(response.content)
                    if 'error' in content:
                        imp.status = 'error'
                        error_msg=content.get('error').get('message')
                        imp.status_msg = error_msg
                        logging.error(error_msg)
                    else:
                        imp.status = 'success'
            else:
                imp.status = 'error'
                imp.status_msg = response.status_code
                try:
                    content = json.loads(response.content)
                    if 'error' in content:
                        error_msg = content.get('error').get('message')
                        imp.status_msg = error_msg
                        logging.error(error_msg)
                except Exception as e:
                    logging.error(content)
        values = {'list_imports': imported}
        path = os.path.join(os.path.dirname(__file__), 'templates/imported.html')
        self.response.out.write(template.render(path, values))


class ImdbImport(object):
    def __init__(self, rating):
        self.rating = rating
        self.status = None
        self.status_msg = ''
        self.rating_id = rating.key().id()


class ImdbLine(object):
    def __init__(self, data):
        # csv reader doesn't handle unicode natively
        self.title = unicode(data[5].decode('UTF-8'))
        self.director = unicode(data[7].decode('UTF-8'))
        self.url = data[15]
        self.score = float(data[8])
        try:
            self.created_time = datetime.strptime(data[2], IMDB_DATETIME_FMT)
            logging.debug("created time {orig} parsed as {time}".format(orig=data[2], time=self.created_time))
        except ValueError as e:
            logging.warn("{exception} parsing {date}".format(exception=e, date=data[2]))
            self.created_time = datetime.now()
        # Runtime in min
        self.runtime = int(data[10])

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
        return ImdbLine(data)


if __name__ == '__main__':
    from google.appengine.api import apiproxy_stub_map, urlfetch_stub

    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
                                            urlfetch_stub.URLFetchServiceStub())
    with open('test/film rating history.csv', 'r') as file:
        csv = ImdbCsvReader(file)
        for rating in csv:
            fb.find_film(rating)
            print('{rating} for {url} on fb #{fb_id}'.format(rating=rating, url=rating.film.imdb_url,
                                                             fb_id=rating.film.fb_id))
