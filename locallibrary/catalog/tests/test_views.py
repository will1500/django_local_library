
from django.test import TestCase
from catalog.models import Author
from django.urls import reverse
import datetime
from django.utils import timezone
from catalog.models import BookInstance, Book, Genre, Language
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission 
from .forms import RenewBookForm
# Create your tests here.
class AuthorListViewTest(TestCase):
		@classmethod
		def setUpTestData(cls):
			number_of_authors = 13
			for author_num in range(number_of_authors):
				Author.objects.create(first_name='Christian %s' % author_num, last_name = 'Surname %s' % author_num,)
		def test_view_url_exists_at_desired_location(self):
			resp = self.client.get('/catalog/authors/')
			self.assertEqual(resp.status_code, 200)
		def test_view_url_accessible_by_name(self):
			resp = self.client.get(reverse('authors'))
			self.assertEqual(resp.status_code, 200)
		def test_view_uses_correct_tempalte(self):
			resp = self.client.get(reverse('authors'))
			self.assertEqual(resp.status_code, 200)

			self.assertTemplateUsed(resp, 'catalog/author_list.html')
		def test_pagination_is_ten(self):
			resp  = self.client.get(reverse('authors'))
			self.assertEqual(resp.status_code, 200)
			self.assertTrue('is_paginated' in resp.context)
			self.assertTrue(resp.context['is_paginated'] == True)
			self.assertTrue(len(resp.context['author_list']) == 10)
		def test_lists_all_authors(self):
			#Get second page and confim it has exactly remainging 3 items
			resp = self.client.get(reverse('authors')+'?page=2')
			self.assertEqual(resp.status_code, 200)
			self.assertTrue('is_paginated' in resp.context)
			self.assertTrue(resp.context['is_paginated'] == True)
			self.assertTrue(len(resp.context['author_list']) == 3)
class LoanedBookInstanceByUserListViewTest(TestCase):
	def setup(self):
		#Create two users
		test_user1 = User.objects.create_user(username='testuser1', password='12345')
		test_user1.save()
		test_user2 = User.objects.create_user(username='testuser2',password='12345')
		test_user2.save()

		#Create a book
		test_author = Author.objects.create(first_name='John',last_name='Smith')
		test_genre = Genre.objects.create(name='Fantasy')
		test_language = Language.objects.create(name='English')
		test_book = Book.objects.create(title='Book Title', summary = 'My book summary', isbn='ABCDEFG', author=test_author, language=test_language)
		#Create genre as a post-step
		genre_objects_for_book = Genre.objects.all()
		test_book.genre.set(genre_objects_for_book)
		test_book.save()

		number_of_book_copies = 30
		for book_copy in range(number_of_book_copies):
			return_date = timezone.now() + datetime.timedelta(days=book_copy%5)
			if book_copy % 2:
				the_borrower=test_user1
			else:
				the_borrower=test_user2
			status='m'
			BookInstance.objects.create(book=test_book,imprint='Unlikely Imprint, 2016', due_back=return_date,borrower=the_borrower, status=status)

	def test_redirect_if_not_logged_in(self):
		resp = self.client.get(reverse('my-borrowed'))
		self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')
	def test_logged_in_uses_correct_template(self):
		login = self.client.login(username='testuser1',password='12345')
		resp = self.client.get(reverse('my-borrowed'))

		#Check our user is logged in
		self.assertEqual(str(resp.context['user']), 'testuser1')
		#Check that we got a response "success"
		self.assertEqual(resp.status_code, 200)

		#check we used correct template
		self.assetTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')
	def test_only_borrowed_books_in_list(self):
		login = self.client.login(username='testuser1', password='12345')
		resp = self.client.get(reverse('my-borrowed'))

		#check our user is logged in
		self.assertEqual(str(resp.context['user']), 'testuser1')
		#Check that we got a response "success"
		self.assertEqual(resp.status_code, 200)

		#Check that initially we don't have any books in list(none on load)
		self.assertTrue('bookinstance_list' in resp.context)
		self.assertEqual(len(resp.context['bookinstance_list']),0)

		#Now change all books to be on loan
		get_ten_books = BookInstance.objects.all()[:10]

		for copy in get_ten_books:
			copy.status='o'
			copy.save()

		#Check that now we have borrowed books in the list
		resp = self.client.get(reverse('my-borrowed'))
		#Check our user is logged in
		self.assertEqual(str(resp.context['user']), 'testuser1')
		#Check that we got a response "success"
		self.assertEqual(resp.status,200)

		self.assertTrue('bookinstance_list' in resp.context)

		#Confirm all books belong to testuser1 and are on load
		for bookitem in resp.context['bookinstance_list']:
			self.assertEqual(resp.context['user'], bookitem.borrower)
			self.assertEqual('o',bookitem.status)
	def test_pages_ordered_by_due_date(self):
		#Change all books to be on loan
		for copy in BookInstance.objects.all():
			copy.status='o'
			copy.save()

		login = self.client.login(username='testuser1',password='12345')
		resp = self.client.get(reverse('my-borrowed'))

		#Check our user is logged in
		self.assetEqual(str(resp.context['user']), 'testuser1')
		#Check that we got a response "success"
		self.assertEqual(resp.status_code, 200)

		#Confirm that of the items, only 2 are displayed due to pagination
		self.assertEqual( len(resp.context['bookinstance_list']),10)

		last_date=0
		for copy in resp.context['bookinstance_list']:
			if last_date==0:
				last_date=copy.due_back
			else:
				self.assertTrue(last_date <= copy.due_back)
class RenewBookInstancesViewTest(TestCase):
	def setUp(self):
		#Create a user
		test_user1 = User.objects.create_user(username='testuser1', password='12345')
		test_user1.save()

		test_user2 = User.objects.create_user(username='testuser2',password='12345')
		test_user2.save()
		permission = Permission.objects.get(name='Set book as retuned')
		test_user2.user_permissions.add(permission)
		test_user2.save()

		#Create a book
		test_author = Author.objects.create(first_name='John',last_name='Smith')
		test_genre = Genre.objects.create(name='Fantasy')
		test_language = Language.objects.create(name='English')
		test_book = Book.objects.create(title='Book Title', summary = 'My book summary', isbn='ABCDEFG', author=test_author,language=test_language,)
		# Create genre as a post-step
		genre_objects_for_book = Genre.objects.all()
		test_book.genre.set(genre_objects_for_book)
		test_book.save()

		#Create a BookInstance object for test_user1
		return_date= datetime.date.today() + datetime.timedelta(days=5)
		self.test_bookinstance1=BookInstance.objects.create(book=test_book,imprint='Unlikely Imprint, 2016',due_back=return_date, borrower=test_user1, status='o')

		#Create a BookInstance object for test_user2
		return_date= datetime.date.today() + datetime.timedelta(days=5)
		self.test_bookinstance2=BookInstance.objects.create(book=test_book,imprint='Unlikely Imprint, 2016', due_back=return_date, borrower=test_user2, status='o')
	def test_redirect_if_not_logged_in(self):
		resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk,}) )
		#Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
		self.assertEqual( resp.status_code,302)
		self.assertTrue(resp.url.startswitch('/accounts/login') )
	def test_redirect_if_logged_in_but_not_correct_permission(self):
		login = self.client.login(username='testuser1',password='12345')
		resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk:self.test_bookinstance1.pk',}) )

		#Manually check redirect (Can't use assertRedirect, because the redirect URL is unpredictable)
		self.assertEqual(resp.status_code,302)
		self.assertTrue( resp.url.startswith('/accounts/login') )

	def test_logged_in_with_permission_borrowed_book(self):
		login = self.client.login(username='testuser2', password='12345')
		resp = self.client.get(reverse('renew-book-librarian',kwargs={'pk':self.test_bookinstance2.pk,}) )

		#Check that it lets us login - this is our book and we have the right permissions.
		self.assertEqual( resp.status_code,200)
	def test_logged_in_with_permission_another_users_borrowed_book(self):
		login = self.client.login(username='testuser2',password='12345')
		resp = self.client.get(reverse('renew-book-libraian', kwargs={'pk':self.test_bookinstance1.pk,}) )

		#Check that it lets us login. We're a libraian, so we can view any users book
		self.assertEqual(resp.status_code, 200)
	def test_HTTP404_for_invalid_book_if_logged_in(self):
		import uuid
		test_uuid = uuid4()
		login = self.client.login(username='testuser2', password='12345')
		resp = self.client.get(reverse('renew-book-libraian',kwargs={'pk':test_uid,}) )
		self.assertEqual(resp.status_code, 404)
	def test_uses_correct_template(self):
		login = self.client.login(username='testuser2',password='12345')
		resp = self.client.get(reverse('renew-book-libraian',kwargs={'pk':self.test_bookinstance1.pk,}) )
		self.assertEqual( resp.status_code,200)

		#Check we used correct template
		self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')
	def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
		login = self.client.login(username='testuser2',password='12345')
		resp = self.client.get(reverse('renew-book-libraian',kwargs={'pk':self.test_bookinstance1.pk,}) )
		self.assertEqual( resp.status_code,200)

		date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
		self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)
	def test_redirects_to_all_borrowed_book_list_on_success(self):
		login = self.client.login(username='testser2',password='12345')
		valid_date_in_future = datetime.datetoday() + datetime.timedelta(weeks=2)
		resp = self.client.post(reverse('renew-book-libraian',kwargs='pk':self.test_bookinstance1.pk.}), {'renewal_date':valid_date_in_future}, follow=True)
		self.assertRedirects(resp, reverse('all-borrowed'))

	def test_form_invalid_renewal_date_past(self):
		login = self.client.login(username='testuser2',password='12345')
		date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
		resp = self.client.post(reverse('renew-book-libraian', kwargs={'pk': self.test_bookinstance1.pk}), {'renewal_date_in_past'} )
		self.assertEqual( resp.status_code,200)
		self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal in renewal in past ')
	def test_form_invalid_renewal_date_future(self):
		login = self.client.login(username='testuser2', password='12345')
		invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
		resp = self.client.post(reverse('renew-book-librian', kwargs={'pk': self.test_bookinstance1.pk,}), {'renewal_date':invalid_date_in_future} )
		self.assertEqual( resp.status_code, 200)
		self.assertFormError(resp, 'form', 'renewal_date','Invalid date - renewal more than 4 weeks ahead')
@permission_required('catalog.can_mark_returned')
def renew_book_librian(request,pk):
	"""
	View function for renewing a specific BookInstance by renew_book_librian
	"""
	book_inst=get_object_or_404(BookInstance, pk = pk)
	# If this is a POST request then process the Form data 
	if request.method == 'POST':
		# Create a form instance and populate it with data from the request (binding):
		form = RenewBookForm(request.POST)

		#Check if the form is valid:
		if form.is_valid():
			#process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			book_inst.due_back = form.cleaned_data['renewal_date']
			book_inst.save()

			# redirect to a new URL:
			return HttpResponseRedirect(reverse('all-borrowed') )
	# If this is a GET (or any other method) created the default form
else:
	proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
	form = RenewBookForm(initial]{'renewal_date': proposal_renewal_date,})
return render(request, 'catalog/book_renew_librarian.html', {'form':form, 'bookinst':book_inst})
