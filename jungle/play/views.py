from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views import generic
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import *

# Create your views here.

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        sel_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'detail.html', {
            'question': question,
            'error_message': "Please select one choice."
        })
    else:
        sel_choice.votes += 1
        sel_choice.save()

    return HttpResponseRedirect(reverse('play:results', args=(question_id,)))

# using generic view to simply process, equivalent to commented area below
class IndexView(generic.ListView):
    template_name = "index.html"
    contenxt_object_name = 'question_list'

    def get_queryset(self):
        return Question.objects.order_by('-pub_date')[:3]


class DetailView(generic.DetailView):
    template_name = "detail.html"
    model = Question

class ResultView(generic.DetailView):
    template_name = "results.html"
    model = Question


# Below is equivalent to the short code above
# def index(request):
#     latest_qs = Question.objects.order_by('-pub_date')[:5]
#     return render(request, 'index.html', {"question_list": latest_qs})


# def detail(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     # above shortcut is equivalent to below
#     # try:
#     #     question = Question.objects.get(pk=question_id)
#     # except Question.DoesNotExist:
#     #     raise Http404(f"Question does not exist for id={question_id}")
#     return render(request, "detail.html", {'question': question})


# def results(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, 'results.html', {'question': question})

