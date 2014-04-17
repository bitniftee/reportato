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
            fields = ('first_name', 'last_name', 'email')
            custom_headers = {
                'first_name': 'Different header'
            }

        def render_email(self, instance):
            return instance.email.replace('@', '< AT >')

    #### usage example
    >>> from journalists.models import Journalist
    >>> from journalists.reporters import JournalistReporter
    >>> reporter = JournalistReporter()  # by default uses model.objects.all(), can use any queryset
    >>> reporter.rendered_headers()
    [u'Different header', u'Last name', u'Email']
    >>> [row for row in reporter.rendered_rows()]
    [
      [u'Angelica', u'Edlund', u'angelicaedlund <AT> engadget.com'],
      [u'Arnold', u'Ofarrell', u'arnoldofarrell <AT> reddit.com'],
     # ...
    ]


Plans
-----

* Provide generic Class-Based Views to simplify the actual report generation
* Add custom columns that aren't part of a model
* TESTS!
