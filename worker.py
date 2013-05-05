#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"

import logging
import webapp2
import fb
import model
import json

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
        p_type = self.request.get('type')
        if p_type is None:
            p_type = 'other'
            logging.warn("Worker didn't receive video type and assumes other")

        # search film in datastore
        film = model.Film.all().filter('imdb_url =', p_url).get()
        if film is None:
            film = model.build_Film(p_title, p_type, p_director, p_runtime, p_url)
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

        try:
            content = json.loads(response.content)
            if u'error' in content:
                error_msg = content.get('error').get('message')
                logging.error("Worker encounters error " + error_msg)
            elif u'id' in content:
                # update rating with the activity id
                rating.activity_id = long(content.get('id'))
                rating.put()
                logging.debug("Worker has updated rating with OpenGraph #{id}".format(id=rating.activity_id))
            else:
                logging.error("Worker has unexpected response " + response.content)
        except Exception as e:
            logging.error("Worker unexpected exception {exception} with response: {response}".format(exception=e,
                                                                                                     response=response.content))


app = webapp2.WSGIApplication([
                                  ('/worker', ImportWorker)
                              ], debug=True)

logging.getLogger().setLevel(logging.DEBUG)
if __name__ == '__main__':
    app.run()