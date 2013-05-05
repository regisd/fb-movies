#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"
from datetime import datetime

from google.appengine.ext import db

class Film(db.Model):
    '''
    A movie, probably known by Facebook
    '''
    title = db.StringProperty()
    director = db.StringProperty()
    fb_id = db.IntegerProperty()
    imdb_url = db.URLProperty()
    # Duration in min
    runtime = db.IntegerProperty()

    def __str__(self):
        return self.title

def build_Film(title, director, runtime, imdb_url):
    film = Film()
    film.title = title
    film.director = director
    film.imdb_url = imdb_url
    film.runtime = runtime
    return film


class Rating(db.Model):
    '''
    A rating in the application
    '''
    user_id = db.IntegerProperty()
    film = db.ReferenceProperty(Film)
    score = db.FloatProperty()
    scale = db.IntegerProperty()
    normalized_rating = db.FloatProperty()
    created_time = db.DateTimeProperty()

    def __str__(self):
        return '{film} ({score}/{scale})'.format(film=self.film, score=self.score, scale=self.scale,
                                                 norm_rating=self.normalized_rating)

def build_Rating(fb_user_id,  film, score, created_time, scale=10):
    rating = Rating()
    rating.user_id = fb_user_id
    rating.film = film
    rating.score = float(score)
    rating.scale = scale
    rating.created_time = created_time
    rating.normalized_rating = rating.score / rating.scale
    return rating
