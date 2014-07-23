from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse

def index(request):
	#Request the context of the request.
	#The context contains information such as the client's machine details, for example
	context = RequestContext(request)
	#Construct a dictionary to pass to the template engine as its context.
	#Note the key boldmessage is the same as {{ boldmessage }} in the template!
	category_list = Category.objects.order_by('-likes')[:5]
	page_list = Page.objects.order_by('-views')[:5]
	context_dict = {'categories': category_list,
			'pages': page_list,
			}
	
	#We loop through each category returned, and create a URL attribute.
	#This attribute stores an encoded URL (e.g. spaces replaced with underscores).
	for category in category_list:
		category.url = encode_url(category)

	for page in page_list:
		page.url 
	
	#Return a rendered response to send to the client.
	#We make use of the shortcut function to make our lives easier.
	#Note that the first parameter is the template we wish to use.
	return render_to_response('rango/index.html', context_dict, context)

def about(request):
	context = RequestContext(request)
	#return HttpResponse("Rango Says: Here is the about page.")
	return render_to_response('rango/about.html', {}, context)

def decode_url(url):
	return url.replace('_', ' ')

def encode_url(url):
	return url.name.replace(' ', '_')

def category(request, category_name_url):
	#Request our context from the request passed to us.
	context = RequestContext(request)

	#Change underscores in the category name to spaces.
	#URLs don't handle spaces well, so we encode them as underscores
	#We can then simply replace the underscores with spaces again to get the name
	category_name = decode_url(category_name_url)

	#Create a context dictionary which we can pass to the templace rendering
	#We start by containing the name of the category passed by the user.
	context_dict = {'category_name': category_name,
			'category_name_url': category_name_url}

	try:
		#Can we find a category with the given name?
		#If we can't, the .get() method raises a DoesNotExist exception
		#So the .get()method returns one model instance or raises an exception.
		category = Category.objects.get(name=category_name)

		#Retrieve all of the associated pages.
		#Note that filter returns >= 1 model isntance
		pages = Page.objects.filter(category=category)

		#Adds ours results list to the templace context under name pages.
		context_dict['pages'] = pages
		#We also add the category object from the database to the context dictionary
		#We'll use this in the templace to verify that the category exists.
		context_dict['category'] = category
	except Category.DoesNotExist:
		#We get here if we didn't find the specified category
		#Don't do anything = the template displays the "no category" message 
		pass
	
	#Go render the response and return it to the client.
	return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
	#Get the context from the request.
	context = RequestContext(request)

	#A HTTP POST?
	if request.method == 'POST':
		form = CategoryForm(request.POST)

		#Have we been provided with a valid form?
		if form.is_valid():
			#Save the new category to the database
			form.save(commit=True)

			#Now call the index() view
			#The user will be shown the homepage
			return index(request)
		else:
			#The supplied form contained errors - print them to the terminal
			print form.errors
	else:
		#If the request was not a POST, display the form to enter details.
		form = CategoryForm()
	
	#Bad form (or form details), no form supplied...
	#Render the form with error messages (if any)
	return render_to_response('rango/add_category.html', {'form': form}, context)

@login_required
def add_page(request, category_name_url):
	#Get the context from the request
	context = RequestContext(request)
	
	category_name = decode_url(category_name_url)

	#A HTTP POST?
	if request.method == 'POST':
		form = PageForm(request.POST)

		if form.is_valid():
			#Cannot commit right away because not all fields are automatically populated
			page = form.save(commit=False)
		
			#Retrieve the associated category object that the page can be added to. Wrapping in a try
			#block to make sure the category exists
			try:
				cat = Category.objects.get(name=category_name)
				page.category = cat
			except Category.DoesNotExist:
				#Go back and render the add category form to show the category does not exist
				return render_to_response('rango/add_category.html', {}, context)
			
			#Set views to default value of 0
			page.views = 0

			#Save the new model instance
			page.save()

			#now that the page is saved, display the category instead
			return category(request, category_name_url)
		else:
			print form.errors
	else:
		#if the request was not a POST, display the form to enter details	
		form = PageForm()

	return render_to_response('rango/add_page.html', {'category_name_url': category_name_url, 
				'category_name': category_name, 'form': form},
				context)

def register(request):
	#Like before, get the request's context
	context = RequestContext(request)

	#A boolean value fore telling the template whether the registration was successful
	#Set to false initially. Code changes value to true when registration succeeds
	registered = False

	#If it's a HTTP POST, we're interested in process form data.
	if request.method == 'POST':
		#Attempt to grab information from the raw form information
		#Not that we make use of both UserForm and UserProfileForm
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		#If the two forms are valid...
		if user_form.is_valid() and profile_form.is_valid():
			#Save the user's form data to the database.
			user = user_form.save()

			#Now we hash the password with the set_password method.
			#Once hashed, we can update the user object.
			user.set_password(user.password)
			user.save()

			#Now sort out the UserProfile instance.
			#Since we need to set the user attribute ourselves, we set commit=False.
			#This delays saving the model until we're ready to avoid integrity problems.
			profile = profile_form.save(commit=False)
			profile.user = user

			#Did the user provide a profile picture?
			#If so, we need to get it from the input from and put it in the UserProfile model.
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			#Now we save the UserProfile model instance.
			profile.save()

			#Update our variable to tell the template registration was successful.
			registered = True

		#Invalid form or forms, Print problem to terminal to show to user
		else:
			print user_form.errors, profile_form.errors

	#Not a HTTP POST, so we render our form using two ModelForm instances.
	#These forms will be blank, ready for user input.
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()

	#Render the template depending on the context.
	return render_to_response('rango/register.html',
		{'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)

def user_login(request):
	#obtain context for user's request
	context = RequestContext(request)

	#If the reqeust ia aHTTP POST, try a to pull out the relevant information
	if request.method == 'POST':
		#Gather ther username and password by the user from login form
		username = request.POST['username']
		password = request.POST['password']

		#Use Django's machinery to attempt to see if username/pass is valid
		#A user object is returned
		user = authenticate(username=username, password=password)

		#If we ahve a user object, the details are correct
		#If none, no user with matching values was found
		if user:
			#Is the account active? It could have been disabled.
			if user.is_active:
				#If the account is valid and active, log user in
				#Send user back to homepage
				login(request, user)
				return HttpResponseRedirect('/rango/')
			else:
				#An inactive account was used - no logggin in
				return HttpResponseRedirect("Your Rango account is disabled.")
		else:
			#Bad login details were provided. 
			print "Invalid login details : {0}, {1}".format(username, password)
			return HttpResponse("Invalid lgoin details supplied.")
	
	#The request is not an HTTP POST, so display loginform.
	else:
		#No context variable to pass to the templay system, hence blank dictionary object
		return render_to_response('rango/login.html', {}, context)

@login_required
def restricted(request):
	#return HttpResponse("Since you're logged in, you can see this text!")
	context = RequestContext(request)
	return render_to_response('rango/restricted.html', {}, context)

#Use the login_required() decorator to ensure only those logged in can access 
#restricted content
@login_required
def user_logout(request):
	#Since we know the user is logged in, we can now just log them out
	logout(request)

	#Take the user back to the homepage
	return HttpResponseRedirect('/rango/')
