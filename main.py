#!/usr/bin/env python
import webapp2, os, jinja2, re, user_blog
#Template information
template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(template_dir))

from google.appengine.ext import db
from google.appengine.api import memcache

class Blog(db.Model):
	title = db.StringProperty(required = True)
	link = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	date_created = db.DateTimeProperty(auto_now_add = True)
	user_created = db.IntegerProperty()
	tags = db.StringListProperty()


class MainHandler(user_blog.BaseHandler):
    def get(self):
    	x = Blog.all()
        self.render("index.html", param = x, logged= user_blog.is_editor(self))

class Single_view(user_blog.BaseHandler):
    def get(self, ide):
    	x = db.Query(Blog).filter('link =', ide).get()
    	#x = Blog.get_by_id(int(ide))
        self.render("single_post.html", post = x, logged= user_blog.is_editor(self))

class Edit(user_blog.BaseHandler):
    @user_blog.user_required
    def get(self, ide):
    	x = Blog.get_by_id(int(ide))
        self.render("edit.html", post = x, logged= user_blog.is_editor(self))


    @user_blog.user_required
    def post(self, ide):
    	post = Blog.get_by_id(int(ide))
    	post.title = self.request.POST['title']
    	post.content = self.request.POST['content']
    	post.tags = re.split('\W+', self.request.POST['tags'])
    	post.put()
        self.redirect("/post/"+ide)


class Add(user_blog.BaseHandler):

    @user_blog.user_required
    def get(self):
        self.render("add.html", logged= user_blog.is_editor(self))

    @user_blog.user_required
    def post(self):
    	auth = self.auth
        author = auth.get_user_by_session()['user_id']
    	post = Blog(user_created= author,title= self.request.POST['title'], content= self.request.POST['content'], tags= re.split('\W+', self.request.POST['tags']), link= self.request.POST['link'])
    	post.put()
    	self.render("message.html", message="Post was added!", link="/post/"+str(post.link), messagetitle="Added!")

class Delete(user_blog.BaseHandler):
    @user_blog.user_required
    def get(self, ide):
    	post = Blog.get_by_id(int(ide))
        post.delete()
        self.render("message.html", message="Post was deleted!", link="/", messagetitle="Delete!")


app = webapp2.WSGIApplication([
    webapp2.Route('/', handler=MainHandler),
    webapp2.Route('/post/<ide>', handler=Single_view),
    webapp2.Route('/admin/edit/<ide>', handler=Edit),
    webapp2.Route('/admin/add', handler=Add),
    webapp2.Route('/admin/delete/<ide>', handler=Delete),
    webapp2.Route('/admin/signup', handler=user_blog.Signup), webapp2.Route('/admin/login', handler=user_blog.Login),
    webapp2.Route('/admin/logout', handler=user_blog.LogoutHandler),
    
], debug=True, config = user_blog.config)