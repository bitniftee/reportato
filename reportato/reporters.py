from django.core.exceptions import FieldError
from django.db.models import Manager
from django.db.models.fields import FieldDoesNotExist
from django.utils.datastructures import SortedDict

# This pattern with options and metaclasses is very similar to Django's
# ModelForms. The idea is to keep a very similar API

class UndefinedField(Exception):
    pass

class ModelReporterOptions(object):

    def __init__(self, options=None):
        """
        Options class to mimic Django's Meta class on forms. So we'll be able
        to define something like

        class MyReporter(ModelReporter):
            class Meta:
                model = MyModel
                fields = ('some', 'stuff')
                custom_headers = {'some': 'Different header'}
        """
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.custom_headers = getattr(options, 'custom_headers', None)


class ModelReporterMetaclass(type):

    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, ModelReporter)]
        except NameError:
            # We are defining ModelReporter itself.
            parents = None

        new_class = super(ModelReporterMetaclass, cls).__new__(
            cls, name, bases, attrs)

        if not parents:
            return new_class

        opts = new_class._meta = ModelReporterOptions(
            getattr(new_class, 'Meta', None))
        if opts.model:
            all_model_fields = [field.name for field in opts.model._meta.fields]
            if opts.fields is None:
                new_class.fields = all_model_fields
            else:
                new_class.fields = opts.fields

            headers = []
            for field_name in new_class.fields:
                try:
                    field = opts.model._meta.get_field_by_name(field_name)[0]
                    header_title = field.verbose_name.capitalize()
                except (AttributeError, FieldDoesNotExist):  # this field doesn't have verbose_name
                    header_title = field_name.replace('_', ' ').capitalize()

                headers.append((field_name, header_title))

            new_class.headers = SortedDict(headers)
            if opts.custom_headers is not None:
                missing_headers = set(opts.custom_headers.keys()) - set(new_class.fields)
                if missing_headers:
                    message = 'Unknown header(s) (%s) specified for %s'
                    message = message % (', '.join(missing_headers),
                                         opts.model.__name__)
                    raise FieldError(message)
                new_class.headers.update(opts.custom_headers)

        return new_class


class ModelReporter(object):
    __metaclass__ = ModelReporterMetaclass

    def __init__(self, items=None, visible_fields=None):
        """
        `items` is expected to be an iterable with Django model instances,
        this covers both a Queryset or a list of items

        `visible_fields` is an optional iterable of fields that should be
        outputted on this instance of ModelReporter. If none, then all
        fields are included.
        """
        if not items:
            items = self._meta.model.objects.all()
        self.items = items

        if not visible_fields:
            visible_fields = self.fields
        self.visible_fields = visible_fields

    def get_header_row(self):
        """
        Returns a sorted list with the field's headers
        """
        return [v for k, v in self.headers.iteritems() if k in self.visible_fields]

    def get_rows(self):
        """
        Returns an iterable with the different rows of the given queryset / list
        """
        for item in self.items:
            yield self.get_row(item).values()

    def get_row(self, instance):
        """
        Returns a soreted dictionary with a single row
        """
        return SortedDict([(name, self._render_field(instance, name)) for name in self.fields and self.visible_fields])

    def _default_field_renderer(self, instance, name):
        """
        Handler for default fields
        """
        if not hasattr(instance, name):
            message = 'Can\'t resolve field %(field)s. You may need to ' \
                'implement the method `get_%(field)s_column(instance)` ' \
                'on your reporter class.'
            raise UndefinedField(message % {'field': name})

        value = getattr(instance, name, None)

        if value is None:
            return u''
        if isinstance(value, Manager):
            return u', '.join(map(unicode, value.all()))

        return unicode(value)

    def _render_field(self, instance, name):
        """
        Field handler
        """
        if hasattr(self, 'get_%s_column' % name):
            return getattr(self, 'get_%s_column' % name)(instance)
        else:
            return self._default_field_renderer(instance, name)
