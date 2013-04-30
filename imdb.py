#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = "Régis Décamps"
import webapp2
import csv

EXPECTED_FIRST_LINE = '"position","const","created","modified","description","Title","Title type","Directors","You rated","IMDb Rating","Runtime (mins)","Year","Genres","Num. Votes","Release Date (month/day/year)","URL"'


class ImdbImporter(webapp2.RequestHandler):
    def post(self):
        csv = ImdbCsvReader(self.request.POST.multi['rating_history'].file)
        o = self.response.out
        o.write('<p>Importing&hellip;</p><ul>')
        for film in csv:
            o.write('<a href="{url}">{title}</a> {note}/10'.format( title=film[5], note=film[8], url=film[15]))
        o.write('</ul>')

class ImdbCsvReader(object):
    def __init__(self, file):
        first_line = file.readline()
        if first_line.strip() != EXPECTED_FIRST_LINE:
            raise ValueError("The file must be a IMDb CSV export")
        self.csv = csv.reader(file, delimiter=',', quotechar='"')

    def __iter__(self):
        return self

    def next(self):
        return self.csv.next()


if __name__ == '__main__':
    with open('test/film rating history.csv', 'r') as file:
        csv = ImdbCsvReader(file)
        for film in csv:
            print("<p>Line: " + ','.join(film) + "</p>")
            print('{title} ({note}/10) {url}'.format( title=film[5], note=film[8], url=film[15]))
