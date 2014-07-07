from django.http import HttpResponse
from django.views.generic import ListView

from .utils import UnicodeWriter


class BaseCSVGeneratorView(ListView):
    writer_class = UnicodeWriter
    file_name = 'myreport.csv'

    def get_reporter_class(self):
        return self.reporter_class

    def get_reporter(self):
        reporter_class = self.get_reporter_class()
        return reporter_class(self.get_queryset())

    def get_writer_class(self):
        return self.writer_class

    def should_write_header(self):
        return getattr(self, 'WRITE_HEADER', True)

    def write_csv(self, fh):
        writer_class = self.get_writer_class()
        writer = writer_class(fh)
        reporter = self.get_reporter()

        if self.should_write_header():
            writer.writerow(reporter.get_header_row())

        writer.writerows(reporter.get_rows())

    def get_file_name(self):
        return self.file_name

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.get_file_name()
        self.write_csv(response)

        return response
