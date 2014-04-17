Reportato
=========

The goal of Reportato is to provide a Django-ish approach to easily get CSV or
Google Spreadsheet generated reports.

This is still a very alpha version, and this documentation may lie

Basic configuration
-------------------

Reportato copies form Django's ModelForms the way to declare how your report
will look like:

    #### reporters.py

    from reportato.reporters import ModelReporter

    from .models import Journalist

    class JournalistReporter(ModelReporter):

        class Meta:
            model = Journalist
            fields = ('first_name', 'last_name', 'something_else')
            custom_headers = {
                'first_name': 'Different header'
            }

        def render_something_else(self):
            # do something smart and return a string
            return 'looks cool'

    #### usage example
    >>> from journalists.models import Journalist
    >>> from journalists.reporters import JournalistReporter
    >>> x = JournalistReporter(instance=Journalist.objects.all()[0])
    >>> x.rendered_fields()
    {'first_name': u'Angelica', 'last_name': u'Edlund', 'something_else', 'looks cool'}
    >>> x.rendered_headers()
    {'first_name': u'Different header', 'last_name': u'Last name', 'something_else', 'Something else'}

Plans
-----

* Provide generic Class-Based Views to simplify the actual report generation
* Report generation will be done potentially using an iterable object instead,
  like a Queryset or a list. I believe that makes more sense.
* Add custom columns that aren't part of a model
* TESTS!
