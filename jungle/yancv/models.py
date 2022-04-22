from django.db import models

# import functions for Coursera courses after classes

class CvExp(models.Model):
    display_order = models.IntegerField("Display order")
    enabled = models.BooleanField("Enabled", default=True)
    row1 = models.CharField("Title Row", max_length=999, blank=False)
    row2 = models.CharField("Row 2", max_length=999, blank=True)
    row3 = models.CharField("Detail row sep by vert", max_length=999, blank=True)
    row4 = models.CharField("Extra row4", max_length=999, blank=True)
    row5 = models.CharField("Extra row5", max_length=999, blank=True)

    def row3_as_lit(self):
        return self.row3.split('|')

class CvCert(models.Model):
    display_order = models.IntegerField("Display order")
    enabled = models.BooleanField("Enabled", default=True)
    icon_tag = models.CharField("Icon", max_length=99, blank=True)
    title = models.CharField("Title", max_length=200, blank=False, primary_key=True)
    title_extra = models.CharField("Title Extra[Superscript]", max_length=200, blank=True)
    issuer = models.CharField("Organizer/Issuer", max_length=200, blank=True)
    courses = models.TextField("Courses sep by vert", max_length=65535, blank=True)
    details = models.CharField("Extra Details", max_length=999, blank=True)
    imgname = models.CharField("Certificate filename", max_length=99, blank=True)
    verify_link = models.CharField("Verification url", max_length=999, blank=True)

    def courses_as_list(self):
        return self.courses.split('|')
    def n_courses(self):
        return len(self.courses.split('|'))

