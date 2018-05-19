from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse 
import datetime 
from .forms import RenewBookForm
from .models import Author
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy


def index(request):
	"""
	View function for home page of site.
	"""
	num_books=Book.objects.all().count()
	num_instances=BookInstance.objects.all().count()
	num_instances_available=BookInstance.objects.filter(status__exact='a').count()
	num_authors=Author.objects.count()

	#Number of visits to this view, as counted in the session
	num_visits=request.session.get('num_visits',0)
	request.session['num_visits'] = num_visits+1


	return render(
		request,
		'index.html',
		context={'num_books':num_books,'num_instances':num_instances,'num_instances_available':num_instances_available,'num_authors':num_authors,'num_visits':num_visits},
		
		)
# Create your views here.
class BookListView(generic.ListView):
	model = Book
	paginate_by = 2
class BookDetailView(generic.DetailView):
	model = Book
class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
	"""
	Generic class-based view listing books on loan to current user.
	"""
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 2

	def get_queryset(self):
		return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
	"""
	View function for renewing a specific BookInstance by libraian
	"""
	book_inst=get_object_or_404(BookInstance, pk=pk)

	if request.method == 'POST':
		form = RenewBookForm(request.POST)

		if form.is_valid():
			book_inst.due_back = form.cleaned_data['renewal_date']
			book_inst.save()

			return HttpResponseRedirect(reverse('catalog'))
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

	return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})
class AuthorCreate(CreateView):
	model = Author
	fields = '__all__'
	initial={'date_of_death':'05/01/2018',}
class AuthorUpdate(UpdateView):
	model = Author
	fields = ['first_name', 'last_name','date_of_birth','date_of_death']
class AuthorDelete(DeleteView):
	model = Author 
	success_url = reverse_lazy('authors')