# Copyright 2012, Matthew Terenzio
# http://journalab.com/

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import pymongo
import string
import json
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httputil

from bottle import route, request, response
from pymongo import Connection, GEO2D
from bson import json_util
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mongo_host", default="127.0.0.1", help="mongodb host")
define("mongo_port", default=27017, help="mongodb port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Home),
            (r"/search", Search),
            (r"/item", Item),
            (r"/feed", Feed),
            (r"/install", Install),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
        tornado.web.Application.__init__(self, handlers, **settings)        
        connection = pymongo.Connection(host=options.mongo_host, port=options.mongo_port, safe=True)
        self.mongo = connection.geopoints

class Search(tornado.web.RequestHandler):
    def get(self):
        coordlist = string.split(self.get_argument("coords"), ',')
        coords = [float(i) for i in coordlist]
        radius = int(self.get_argument("radius"))
        limit = self.get_argument("limit", None)
        if limit == None:
            limit = 100
        else:
            limit = int(limit)              
        collection = self.application.mongo.items         
        try:
            cursor = collection.find({"loc": {"$within": {"$center": [coords, radius]}}}, {'_id': False}).limit(limit)
            results = []
            for result in cursor:
               results.append(result)
            self.write(str(json.dumps({'results': results},default=json_util.default)))
        except:
            self.write("Error trying to read collection:", sys.exc_info()[0])

class Item(tornado.web.RequestHandler):
    def post(self):
        try:
            json_data = json.loads(self.request.body)
        except ValueError:
            raise tornado.httpserver._BadRequestException(
                "Invalid JSON structure."
            )
        item = self.request.body                
        collection = self.application.mongo.items         
        collection.insert({"item": item})

class Feed(tornado.web.RequestHandler):
    def post(self):
        try:
            json_data = json.loads(self.request.body)
        except ValueError:
            raise tornado.httpserver._BadRequestException(
                "Invalid JSON structure."
            )
        feed = self.request.body                
        collection = self.application.mongo.feeds         
        collection.insert({"feed": feed})


class Home(tornado.web.RequestHandler):
    def get(self):
        self.write("geopoints - http://geopoints.org")
        
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
