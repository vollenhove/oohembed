"""oohEmbed
Your one-stop oEmbed provider

See http://code.google.com/p/oohembed/
and http://oohembed.com/

Copyright (c) 2008, Deepak Sarda

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following
    disclaimer in the documentation and/or other materials provided
    with the distribution.

  * Neither the name of the oohEmbed project nor the names of its 
    contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import wsgiref.handlers
import logging
import os
import urllib

from google.appengine.ext import webapp
from jinja import Environment, FileSystemLoader

from provider import Provider

class EndPoint(webapp.RequestHandler):
    providers = Provider.get_providers()

    def get(self):

        query_url = urllib.unquote(self.request.get('url').encode('utf-8'))
        resp_format = self.request.get('format', default_value='json')

        if 'Development' in os.environ['SERVER_SOFTWARE']:
            self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        else:
            self.response.headers['Content-Type'] = 'application/json'

        if not query_url:
            self.error(400)
            self.response.out.write('Missing url parameter in request')
            return

        if not resp_format in ['json', 'jsonp']:
            self.error(501)
            self.response.out.write('Only json format is currently supported')
            return 

        callback = self.request.get('callback').encode('utf-8')
        # TODO: Make sure callback name here is a valid Javascript
        # variable name using a whitelist. Otherwise raise 400

        extra_params = {}
        if self.request.get('maxwidth'):
            extra_params['maxwidth'] = self.request.get('maxwidth').encode('utf-8')
        if self.request.get('maxheight'):
            extra_params['maxheight'] = self.request.get('maxheight').encode('utf-8')

        for p in self.providers:
            resp = p.provide(query_url, extra_params)
            if resp:
                break

        if not resp:
            self.error(404)
            self.response.out.write('Could not determine suitable ' +
                    'representation for queried URL')
            return

        if callback:
            self.response.headers['Content-Type'] = 'text/javascript'
            self.response.out.write('%s(%s);' % (callback, resp))
        else:
            self.response.out.write(resp)

        return
            
class MainPage(webapp.RequestHandler):
    providers = Provider.get_providers()

    def get(self):

        providers = [{'title': p.title, 'url': p.url, \
                    'example_url': p.example_url, \
                    'description': p.__doc__} \
                        for p in self.providers]
        providers.sort(lambda x, y: cmp(x['title'], y['title']))
                 
        if 'Development' in os.environ['SERVER_SOFTWARE']:
            production = False
        else:
            production = True

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        tmpl = env.get_template('index.jinja')

        hostname = os.environ['HTTP_HOST'].lower()
        self.response.out.write(tmpl.render(providers=providers,
                        production=production, hostname=hostname))

urls = [('/', MainPage),
        ('/oohembed\/?', EndPoint)]

def main():
    application = webapp.WSGIApplication(
          urls, debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
