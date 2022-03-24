from django.contrib import admin
from .models import Choice, Question
# Register your models here.

# default approach (all fields)
# admin.site.register(Choice)

# order, name and select fields 
# put related tables in the same page
class ChoiceInline(admin.TabularInline): # or admin.StackedInline
    model = Choice
    extra = 2

class QuestionAdmin(admin.ModelAdmin):
    # marking up some fields
    fieldsets = [
        ('Question',         {'fields': ['q_text']}),
        ('Date information', {'fields': ['pub_date']}),
    ]
    # add the relevant tables
    inlines = [ChoiceInline]
    # show more details in list, function can also be listed
    # further touching of class function in model.py @admin.display
    list_display = ('q_text', 'pub_date', 'is_recent')
    # add a filter box in the right
    list_filter = ['pub_date']
    

    



admin.site.register(Question, QuestionAdmin)

