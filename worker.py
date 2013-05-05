#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"

import logging
import webapp2
import fb
import model
from datetime import datetime

DATETIME_ISO = '%Y-%m-%dT%H:%M:%S'


class ImportWorker(webapp2.RequestHandler):
    def post(self):
        fb_user_id = long(self.request.get('fb_user_id'))
        fb_access_token = self.request.get('fb_access_token')

        p_url = self.request.get('url')
        p_title = self.request.get('title')
        p_director = self.request.get('director')
        p_runtime = int(self.request.get('runtime'))
        p_score = float(self.request.get('score'))
        p_created_time = datetime.strptime(self.request.get('created_time'), DATETIME_ISO)

        # search film in datastore
        film = model.Film.all().filter('imdb_url =', p_url).get()
        if film is None:
            film = model.build_Film(p_title, p_director, p_runtime, p_url)
            fb.find_film(film)
            # TODO if film not found, ask cotribution
            film.put()

        # find existing rating
        rating = model.Rating.all().filter('film = ', film).filter('user_id = ', fb_user_id).get()
        if not rating:
            rating = model.build_Rating(fb_user_id, film, p_score, p_created_time)
            # save in datastore
            rating.put()

        # TODO approve app so that it can watch for the user
        # fb.post_watch(rating, fb_access_token)
        response = fb.post_rating(rating, fb_access_token)

        if response.status_code != 200:
            try:
                import json

                content = json.loads(response.content)
                if 'error' in content:
                    error_msg = content.get('error').get('message')
                    logging.error(error_msg)
            except Exception as e:
                logging.error(content)


app = webapp2.WSGIApplication([
                                  ('/worker', ImportWorker)
                              ], debug=True)

logging.getLogger().setLevel(logging.DEBUG)
if __name__ == '__main__':
    app.run()