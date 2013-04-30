#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"
import webapp2


class ImdbImporter(webapp2.RequestHandler):
    def post(self):
        f = self.request.POST.multi['rating_history'].file
        for line in f:
            print("Line: " + line)

