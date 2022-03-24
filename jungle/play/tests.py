import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Question


def create_question(question_text, days):
    """create a test question based on inupt futrue"""
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(q_text=question_text, pub_date=time)


class QuestionModelTests(TestCase):

    def test_is_recent_for_future(self):
        """futre question should NOT be return in is_recent"""
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.is_recent(), False)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """When no question, check message"""
        response = self.client.get(reverse('play:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No published question available.")
        self.assertQuerysetEqual(response.context['question_list'], [])

    def test_past_question(self):
        """Already published questions"""
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('play:index'))
        self.assertQuerysetEqual(
            response.context['question_list'],
            [question],
        )

    def test_future_question(self):
        """Future question should NOT displaye"""
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('play:index'))
        self.assertContains(response, "No published question available.")
        self.assertQuerysetEqual(response.context['question_list'], [])

    def test_future_question_and_past_question(self):
        """Both future and past question created, should one show past"""
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('play:index'))
        self.assertQuerysetEqual(
            response.context['question_list'],
            [question],
        )

    def test_two_past_questions(self):
        """The questions index page may display multiple questions."""
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('play:index'))
        self.assertQuerysetEqual(
            response.context['question_list'],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """The detail view of a FUTURE question should returns a 404"""
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('play:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """Published question should return correct result"""
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('play:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.q_text)