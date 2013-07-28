# coding: utf-8
import os
import urllib2
from urllib2 import URLError
import tornado.httpserver
import tornado.database
import tornado.ioloop
import tornado.options
import tornado.web
import socket

from tornado.options import define, options
from pyquery import PyQuery

define("port", default=8080, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="mamba database host")
define("mysql_database", default="lp", help="mamba database name")
define("mysql_user", default="root", help="mamba database user")
define("mysql_password", default="", help="mamba database password")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/status", StatusHandler),
            (r"/profiles_count", ProfilesCountHandler),
            (r"/viewed_profiles_count", ViewedProfilesCountHandler),
            (r"/liked_profiles_count", LikedProfilesCountHandler),
            (r"/get_profiles", GetProfilesHandler),
            (r"/visit_profiles", VisitProfilesHandler),
            (r"/like_profiles", LikeProfilesHandler),
            (r"/unvisit_profiles", UnvisitProfilesHandler),
            (r"/unlike_profiles", UnlikeProfilesHandler)
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=False
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def my_session(self):
        return self.get_cookie('ext_session', '').replace('%','%%')

    def get_unviewed_profiles_count(self):
        return self.db.get("SELECT COUNT(*) as profiles_count FROM profiles WHERE viewed = 0 and session='%s'" % self.my_session)

    def get_viewed_profiles_count(self):
        return self.db.get("SELECT COUNT(*) as profiles_count FROM profiles WHERE viewed = 1 and session='%s'" % self.my_session)


    def get_unliked_profiles_count(self):
        return self.db.get("SELECT COUNT(*) as profiles_count FROM profiles WHERE liked != 1 and session='%s'" % self.my_session)

    def get_liked_profiles_count(self):
        return self.db.get("SELECT COUNT(*) as profiles_count FROM profiles WHERE liked = 1 and session='%s'" % self.my_session)

    def save_profiles(self, profiles):
        for profile in profiles:
            try:
                self.db.execute("INSERT INTO profiles (url, session) VALUES ('%s', '%s')" % (profile['url'], self.my_session))
            except Exception:
                pass

    def get_unviewed_profiles(self):
        return self.db.query("SELECT * FROM profiles WHERE viewed = 0 and session='%s' LIMIT 10" % self.my_session)

    def get_unliked_profiles(self):
        return self.db.query("SELECT * FROM profiles WHERE liked = 0 and viewed = 1 and session='%s' LIMIT 10" % self.my_session)

    def set_profile_viewed(self, id):
        self.db.execute("UPDATE profiles set viewed = 1 where id = %d and session='%s'" % (id, self.my_session))

    def delete_profile(self, id):
        self.db.execute("DELETE from profiles where id = %d and session='%s'" % (id, self.my_session))

    def set_profile_liked(self, id):
        self.db.execute("UPDATE profiles set liked = 1 where id = %d and session='%s'" % (id, self.my_session))

    def set_profiles_unviewed(self):
        self.db.execute("UPDATE profiles set viewed = 0 and session='%s'" % self.my_session)


    def set_profiles_unliked(self):
        self.db.execute("UPDATE profiles set liked = 0 and session='%s'" % self.my_session)


class StatusHandler(BaseHandler):
    def get(self):
        self.write("OK")


class IndexHandler(BaseHandler):
    def get(self):
        self.render("home.html")


class ProfilesCountHandler(BaseHandler):
    def get(self):
        self.write(self.get_unviewed_profiles_count())


class ViewedProfilesCountHandler(BaseHandler):
    def get(self):
        self.write(self.get_viewed_profiles_count())


class LikedProfilesCountHandler(BaseHandler):
    def get(self):
        self.write(self.get_liked_profiles_count())


class GetProfilesHandler(BaseHandler):
    def post(self):
        arg = self.request.arguments
        #http://loveplanet.ru/?a=search&d=1&pol=1&spol=2&bage=18&tage=28&foto=1&country=3159&region=4312&city=4400&relig=0&p=1&ajax=1
        search_url = 'http://loveplanet.ru/?a=search&d=1&pol=1&spol=2&bage=' + arg['fromAge'][0] + '&tage=' + arg['toAge'][0] + '&foto=1&country=3159&' + arg['fromCity'][0] + '&relig=0&ajax=1&p=' + arg['page'][0]

        req = urllib2.Request(search_url)
        req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')
        req.add_header('Cookie', 'domhit=1; oper=megafom; randomhit=774133585; CP.mode=B; LP_CH_C=love_cookies; session=' + self.my_session)

        r = urllib2.urlopen(req)
        page_html = r.read()

        whole_page = PyQuery(page_html)

        next_page = whole_page('.search_nav').eq(0).next('a').eq(0).attr('href').split("/")
        next_page = next_page[-2].split("-")
        next_page = next_page[-1]

        profiles_html = whole_page('.biglist_row')
        profiles = []
        for profile in profiles_html:
            p = PyQuery(profile)
            name = p('.nickname').text()
            url = 'http://loveplanet.ru' + p('.nickname').attr('href')
            profiles.append({'name': name, 'url': url})

        self.save_profiles(profiles)

        response_data = {
            'next_page': next_page
        }

        self.write(response_data)
        r.close()


class VisitProfilesHandler(BaseHandler):
    def get(self):
        profiles = self.get_unviewed_profiles()

        for profile in profiles:
            req = urllib2.Request(profile['url'])
            req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')
            req.add_header('Cookie', 'domhit=1; oper=megafom; randomhit=774133585; CP.mode=B; LP_CH_C=love_cookies; session=' + self.my_session)
            try:
                r = urllib2.urlopen(req,timeout = 2)
            except urllib2.HTTPError, err:
                if err.code == 404:
                    self.delete_profile(profile['id'])

            self.set_profile_viewed(profile['id'])
            try:
                r.read()
                r.close()
            except:
                print 'ooops'


        if self.get_unviewed_profiles_count():
            self.write('Moaaar!')
        else:
            self.write('Im done!')

class LikeProfilesHandler(BaseHandler):
    def get(self):
        profiles = self.get_unliked_profiles()
        for profile in profiles:
            req = urllib2.Request('http://loveplanet.ru/a-search/d-1/pol-1/spol-2/foto-1/item-1//ajax-1/login-' + profile['url'].split('/')[4] + '/likes-1')
            req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')
            req.add_header('Cookie', 'domhit=1; oper=megafom; randomhit=774133585; CP.mode=B; LP_CH_C=love_cookies; ext_session=' + self.my_session)
            try:
                r = urllib2.urlopen(req,timeout = 2)
            except urllib2.HTTPError, err:
                if err.code == 301:
                    self.delete_profile(profile['id'])
            
            self.set_profile_liked(profile['id'])
            try:
                r.close()
            except:
                print 'ooops'

        if self.get_unliked_profiles_count():
            self.write('Moaaar!')
        else:
            self.write('Im done!')


class UnvisitProfilesHandler(BaseHandler):
    def get(self):
        self.set_profiles_unviewed()
        self.write("OK")


class UnlikeProfilesHandler(BaseHandler):
    def get(self):
        self.set_profiles_unliked()
        self.write("OK")


def main():
    """
    Start server
    """
    tornado.options.parse_command_line()

    application = Application()

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
