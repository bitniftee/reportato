# Reportato

The goal of Reportato is to provide a Django-ish approach to easily get CSV or
Google Spreadsheet generated reports.

This is still a very alpha version, and this documentation may lie

## Basic configuration

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

        def get_email_column(self, instance):
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

## Documentation

### Model Reporters

For creating a report for a given model, you just need to write a class that
will inherit from `reportato.reporters.ModelReporter`, and indicate what
model do you want to report with this. A very simple example:

    from reportato.reporters import ModelReporter

    class MyReport(ModelReporter):

        class Meta:
            model = MyModel

By default this will generate reports with every field on `MyModel`. You can
especify what fields to report by using the `fields` variable:

        # ...
        class Meta:
            model = MyModel
            fields = ('field1', 'field2', 'field3')

The header row will be generated based on the model field's `verbose_name` value,
or a simple capitalization of the field name if it doesn't have a `verbose_name`.
If you want to override that, you can do it using `custom_headers`:

        # ...
        class Meta:
            model = MyModel
            custom_headers {
                'field1': 'Very cool header'
            }

Lastly, if you want to change how to represent a field, you can write your
`get_FIELDNAME_column` method to add any logic you want:

    # ...
    def get_field1_column(self, instance):
        return instance.field1.replace('_', '-')

To create the report, you need to instantiate the object using a list of objects
or a queryset. If you do not pass one, it will take all the objects for the
given model:

    >>> MyReport()  # report with MyModel.objects.all()
    >>> MyReport(MyModel.objects.filter(something=something_else))

Other methods:

#### `rendered_headers()`

Returns an ordered list with the CSV headers

#### `rendered_fields(instance)`

Returns a sorted dict with the value of each field for the given `instance`

#### `rendered_rows()`

Returns an iterable with an ordered list of the values for the given fields.

### reportato.views.BaseCSVGeneratorView

Are you a CBV fan? It is your lucky day, because `reportato` provides a base view
from which you can inherit for building your own stuff.

`BaseCSVGeneratorView` inherits from Django's `django.views.generic.ListView`
meaning that it needs a model or a queryset to work with. Internally,
`BaseCSVGeneratorView` will use `get_queryset()` method to resolve the list
of objects to report with.

#### `reporter_class`

Class attribute to define the class of the reporter you are going to use on
this view. Should inherit from `ModelReporter`. If you need to decide what
reporter to use in execution time, override `get_reporter_class()` method
instead.

#### `writer_class`

Class attribute to define the CSV writer class. By default uses `UnicodeWriter`,
as implemented on Python documentation.

#### `WRITE_HEADER`

Flag to determine wether we want in our report the headers or not.

### `file_name`

Class attribute to define the file name for the generated report. If you want
something more dynamic, you should override `get_file_name()` method.

### `write_csv()`

Method that receiving an input flow (`HttpResponse`, `io.BytesIO`...) uses
reporter's method to write into such flow.

## Further examples

### Report as a Google Sheet

The initial plan was to add some feature to automatically create spreadsheet
from given reports. However, I changed my mind during the implementation because
it made certain assumptions about how the tool need to implement OAuth and
felt that it was overkill.

Instead, I'm providing some examples to do it using the tools on this library.
The basic undersanding is that we need to dump the CSV file into a `BytesIO` and
upload it to Google Drive using `google-api-python-client`.

    import io

    # google apiclient dependencies
    import httplib2
    from apiclient.discovery import build
    from apiclient.http import MediaIoBaseUpload

    from reporters.views import BaseCSVGeneratorView
    from .models import MyModel
    from .reports import MyReport

    class MyReportToSpreadsheet(BaseCSVGeneratorView):
        model = MyModel
        reporter_class = MyReport

        def get(self, request, *args, **kwargs):
            outfile = io.BytesIO()
            self.write_csv(outfile)
            # now outfile is filled with the CSV we want.
            # we need to fetch the user credentials using OAuth, not covering it here
            credentials = request.user.oauth_credentials
            http = credentials.authorize(httplib2.Http())

            service = build(
                serviceName='drive',
                version='v2',
                developerKey=settings.GOOGLE_API_KEY,
                http=http
            )

            media_body = MediaIoBaseUpload(
                outfile,
                mimetype='text/csv',
                resumable=False
            )

            body = {
                "title": title,
                "description": description,
                "mimeType": 'text/csv'
            }

            uploaded_file = service.files().insert(
                body=body,
                media_body=media_body,
                convert=True  # to convert CSV's to Spreadsheet
            ).execute()

            return HttpResponseRedirect(uploaded_file['alternateLink'])

## Running tests

Running reportato tests is dead simple. First, you need a `virtualenv`. I
highly recommend to use [`virtualenvrapper`](http://virtualenvwrapper.readthedocs.org/en/latest/)
for it. Having it installed, you'll just need to:

    $ mkvirtualenv reportato  # will create the virtualenv
    $ workon reportato  # will activate the virtualenv
    # deactivate  # will deactivate it

In order to run the tests we need `Django` and `Mock`:

    $ pip install Django Mock

Once those dependencies are installed, you can run the tests simply with:

    $ python runtests.py

## Future plans

* Add custom columns that aren't part of a model for adding aggregates
* Make some sort of Mixin for making the upload to Google Sheets easier
* Use `values_list` instead of composing the models for trying to be more efficient
* Provide helpers for deferring the report generation to GAE task queues
