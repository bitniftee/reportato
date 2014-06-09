# Reportato

The goal of Reportato is to provide a Django-ish approach to easily get CSV or
Google Spreadsheet generated reports.

This is still a very alpha version, and this documentation may lie.

**Note:** Generating a report can take a long time if the table you're
generating your report from is large. You might want to avoid forcing your
users to experience this latency, e.g. by generating the report regularly on a
cron and allowing them to download the most recent copy, or by fetching the
report via AJAX so you can show your user pictures of kittens while they wait.

## Basic configuration

With Reportato, the way you declare how your report should look is similar to
Django's ModelForms:


```python
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
>>> reporter.get_header_row()
[u'Different header', u'Last name', u'Email']
>>> [row for row in reporter.get_rows()]
[
  [u'Angelica', u'Edlund', u'angelicaedlund <AT> engadget.com'],
  [u'Arnold', u'Ofarrell', u'arnoldofarrell <AT> reddit.com'],
 # ...
]
```


## Documentation

### Model Reporters

To create a report for a given model, you just need to write a class that
will inherit from `reportato.reporters.ModelReporter`, and indicate which
model you want to report on. A very simple example:


```python
from reportato.reporters import ModelReporter

class MyReport(ModelReporter):

    class Meta:
        model = MyModel
```


By default this will generate reports with every field on `MyModel`. You can
especify which fields to include by using the `fields` variable:


```python
    # ...
    class Meta:
        model = MyModel
        fields = ('field1', 'field2', 'field3')
```


The header row will be generated based on the model field's `verbose_name` value,
or a simple capitalization of the field name if it doesn't have a `verbose_name`.
If you want to override that, you can do it using `custom_headers`:


```python
    # ...
    class Meta:
        model = MyModel
        custom_headers {
            'field1': 'Very cool header'
        }
```


The way reportato resolves each given field is very simple:

* Checks if the reporter class has some method named `get_FIELDNAME_column(instance)`.
  If it does, uses it. Otherwise:
* Checks if the given `FIELDNAME` is accessible directly through the instance.
* Will raise a `reportato.reporters.UndefinedField` exception if neither
  of those are defined.

What this means is that you can define whatever you want in your report as a field
while you have the proper `get_FIELDNAME_column` method. And also will be able
to use model's fields, decorators or even aggregated fields.

As an example:


```python
    # ...
    def get_field1_column(self, instance):
        return instance.field1.replace('_', '-')
```


To create the report, you need to instantiate the object using a list of objects
or a queryset. If you do not pass one, it will take all the objects for the
given model:


```python
>>> MyReport()  # report with MyModel.objects.all()
>>> MyReport(MyModel.objects.filter(something=something_else))
```



Additionally, you can define what fields you want to see on your report during
creation time using the `visible_fields` parameter:

    >>> MyReport(visible_fields=['first_name', 'last_name'])

This way your reporter will only show those fields, even if you had more on
your Reporter definition. This allows you to build custom logic if the final
user wants to customise what columns he/she wants to see each time.

Other methods:

#### `get_header_row()`

Returns an ordered list with the CSV headers

#### `get_row(instance)`

Returns a sorted dict with the value of each field for the given `instance`

#### `get_rows()`

Returns an iterable with an ordered list of the values for the given fields.

### reportato.views.BaseCSVGeneratorView

Are you a CBV fan? It's your lucky day, because `reportato` provides a base view
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

Flag to determine whether to include the headers in the report or not.

### `file_name`

Class attribute to define the file name for the generated report. If you want
something more dynamic, you should override `get_file_name()` method.

### `write_csv()`

Method that receiving an input flow (`HttpResponse`, `io.BytesIO`...) uses
reporter's method to write into such flow.

## Further examples

### Report as a Google Sheet

The initial plan was to add some features to automatically create spreadsheets
from given reports. However, I changed my mind during implementation because
it made certain assumptions about how the tool needed to implement OAuth and
felt that it was overkill.

Instead, I'm providing some examples of how to do it using this library.
The basic undersanding is that we need to dump the CSV file into a `BytesIO` and
upload it to Google Drive using `google-api-python-client`.


```python
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
```


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
