import webapp2
from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError
import jinja2, os
from webapp2_extras.appengine.auth import models

#Configuration
config = {}
config['webapp2_extras.sessions'] = {'secret_key': 'Secret',}


#Template information
template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_environment = jinja2.Environment(autoescape=True, loader=jinja2.FileSystemLoader(template_dir))


def user_required(handler):
    """
         Decorator for checking if there's a user associated with the current session.
         Will also fail if there's no session present.
     """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            # If handler has no login_url specified invoke a 403 error
            try:
                self.redirect(self.auth_config['login_url'], abort=True)
            except (AttributeError, KeyError), e:
                self.abort(403)
        else:
            return handler(self, *args, **kwargs)

    return check_login


def is_editor(self):
	auth = self.auth
	if not auth.get_user_by_session():
		return False
	else:
		return True

class BaseHandler(webapp2.RequestHandler):
	"""
	BaseHandler for all requests
	Holds the auth and session properties so they are reachable for all requests
	"""

	def write(self, *a, **kw):
		self.response.out.write(*a,**kw)

	def render_str(self, template,**params):
		t= jinja_environment.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template,**kw))


	def display_message(self, message):
		"""Utility function to display a template with a simple message."""
		self.render('message.html', {'message': message})

	def dispatch(self):
		"""
			Save the sessions for preservation across requests
		"""
		try:
			super(BaseHandler, self).dispatch()
		finally:
			self.session_store.save_sessions(self.response)

	@webapp2.cached_property
	def auth(self):
		return auth.get_auth()

	@webapp2.cached_property
	def session_store(self):
		return sessions.get_store(request=self.request)

	@webapp2.cached_property
	def auth_config(self):
		"""
		Dict to hold urls for login/logout
		"""
		return {
			'login_url': self.uri_for('login'),
			'logout_url': self.uri_for('logout')
		}

	@webapp2.cached_property
	def user(self):
		user = self.auth.get_user_by_session()
		return user

	@webapp2.cached_property
	def name_user(self):
		user_model, timestamp =  self.auth.store.user_model.get_by_auth_token(self.user['user_id'], self.user['token']) if self.user else (None, None)
		return user_model.name + " " + user_model.last_name

	@webapp2.cached_property
	def user_model(self):
		user_model, timestamp =  self.auth.store.user_model.get_by_auth_token(self.user['user_id'], self.user['token']) if self.user else (None, None)
		return user_model


class Login(BaseHandler):
    def get(self):
    	if is_editor(self):
    		self.redirect("/")
    	return self.render("login.html")

    def post(self):
        username = self.request.POST.get('email')
        password = self.request.POST.get('password')
        try:
            self.auth.get_user_by_password(username, password)
            self.redirect('/')
        except (InvalidAuthIdError, InvalidPasswordError), e:
        	self.render("message.html", message="Your email or password were not correct!", link="/admin/login", messagetitle="Error!")


class Signup(BaseHandler):
    def get(self):
    	self.redirect("/admin/login")

    def post(self):
    	email = self.request.POST.get('email')
        name = self.request.POST.get('name')
        last_name = self.request.POST.get('lastname')
        password = self.request.POST.get('password')
        
        user = self.auth.store.user_model.create_user(email, email_address = email, name = name, last_name= last_name, password_raw=password)
        if not user[0]:
        	self.render("message.html", message="You have not successfully registered!", link="/admin/login#create", messagetitle="Error!")
        else:
        	self.render("message.html", message="You have successfully registered!", link="/admin/login", messagetitle="Now login!")

class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.render("message.html", message="You have successfully logged out!", link="/", messagetitle="Log out!")