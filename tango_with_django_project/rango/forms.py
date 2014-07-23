from django import forms
from rango.models import Page, Category, UserProfile
from django.contrib.auth.models import User

class CategoryForm(forms.ModelForm):
	name = forms.CharField(max_length=128, help_text="Please enter the category name.")
	views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
	likes = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

	#An inline clas to provide additional information on the form.
	class Meta:
		#Provide an association between the ModelForm and a model
		model = Category
	
class PageForm(forms.ModelForm):
	title = forms.CharField(max_length=128, help_text="Please enter the title of the page.")
	url = forms.URLField(max_length=200, help_text="Please enter the URL of the page.")
	views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

	class Meta:
		#Provide an associated between the ModelForm and a model
		model = Page

		#We only want to include fields that are necessary for the model
		fields = ('title', 'url', 'views')

	def clean(self):
		cleaned_data = self.cleaned_data
		url = cleaned_data.get('url')

		#if url is not empty and doesn't start with 'http://', prepent 'http://'
		if url and not url.startswith('http://'):
			url = 'http://' + url
			cleaned_data['url'] = url
		
		return cleaned_data

class UserForm(forms.ModelForm):
	#this is redefined because the base element displays the password
	#We want to hide the user's input thefore providing our own definition
	#for the password attribute
	password = forms.CharField(widget=forms.PasswordInput())

	class Meta:
		model = User
		fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = ('website', 'picture')


