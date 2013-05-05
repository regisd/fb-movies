#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright Régis Décamps

import os
import logging

import webapp2
import webob
from google.appengine.ext.webapp import template

import imdb
import model


class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request, response)

    def handle_exception(self, exception, debug):
        if isinstance(exception, ValueError):
            self.response.set_status(400)  # bad request
            self.response.write(str(exception))
        elif isinstance(exception, webob.exc.WSGIHTTPException):
            # If the exception is a HTTPException, use its error code.
            self.response.set_status(exception.code)
            self.response.write(exception.html_body({}))
        else:
            # Otherwise use a generic 500 error code.

            # Log the error because I have no idea what it is
            logging.exception(exception)
            self.response.set_status(500)
            # Set a custom message.
            self.response.write('An error occurred. ')
        logging.warn(exception)
        logging.warn("Caused by {cause}".format(cause=exception.args))


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect("/page/index.html")


class RatingHandler(BaseHandler):
    def get(self, id):
        id = long(id)
        rating = model.Rating.get_by_id(id)
        logging.debug("Rating #{id} is {rating}".format(id=id, rating=rating))
        values = {'rating': rating, 'id': id}
        path = os.path.join(os.path.dirname(__file__), 'templates/rating.html')
        self.response.out.write(template.render(path, values))


app = webapp2.WSGIApplication([
                                  ('/', MainHandler),
                                  ('/imdb', imdb.ImdbImporter),
                                  webapp2.Route(r'/rating/<id:\d+>', handler=RatingHandler)
                              ], debug=True)

logging.getLogger().setLevel(logging.DEBUG)
if __name__ == '__main__':
    app.run()