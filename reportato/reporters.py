from django.core.exceptions import FieldError

# This pattern with options and metaclasses is very similar to Django's
# ModelForms. The idea is to keep a very similar API

class ModelReporterOptions(object):

    def __init__(self, options=None):
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
            all_model_fields = opts.model._meta.get_all_field_names()
            if opts.fields is None:
                new_class.fields = all_model_fields
            else:
                missing_fields = set(opts.fields) - set(all_model_fields)
                if missing_fields:
                    message = 'Unknown field(s) (%s) specified for %s'
                    message = message % (', '.join(missing_fields),
                                         opts.model.__name__)
                    raise FieldError(message)
                new_class.fields = opts.fields

            new_class.headers = {
                field_name: opts.model._meta.get_field_by_name(field_name)[0].verbose_name.capitalize()
                for field_name in new_class.fields
            }
            if opts.custom_headers is not None:
                missing_headers = set(opts.custom_headers.keys()) - set(all_model_fields)
                if missing_headers:
                    message = 'Unknown header(s) (%s) specified for %s'
                    message = message % (', '.join(missing_headers),
                                         opts.model.__name__)
                    raise FieldError(message)
                new_class.headers.update(opts.custom_headers)

        return new_class


class ModelReporter(object):
    __metaclass__ = ModelReporterMetaclass

    def __init__(self, instance):
        if not isinstance(instance, self._meta.model):
            raise ValueError('The given object is not an instance of %s' %
                self._meta.model.__name__)

        self.instance = instance

    def rendered_headers(self):
        return [self.headers[field] for field in self.fields]

    def rendered_fields(self):
        return {name: self._render_field(name) for name in self.fields}

    def _render_field(self, name):
        if hasattr(self, 'render_%s' % name):
            return getattr(self, 'render_%s' % name)()
        else:
            return unicode(getattr(self.instance, name))
