#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"
from datetime import datetime


class Film(object):
    def __init__(self, title, id):
        self.title = title
        # can be the URL of an opengraph objector a fb id
        self.id = id
        self.time_length = 0

    def __str__(self):
        return self.title


class Rating(object):
    def __init__(self, film, rating, scale=10):
        self.film = film
        self.score = float(rating)
        self.scale = scale
        self.created_time = datetime.now()

    @property
    def normalized_rating(self):
        return self.score / self.scale

    def __str__(self):
        return '{film} ({score}/{scale})'.format(film=self.film, score=self.score, scale=self.scale, norm_rating=self.normalized_rating)