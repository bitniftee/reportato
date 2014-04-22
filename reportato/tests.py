from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.test import TestCase

from .reporters import ModelReporter


class ModelReporterMetaclassTestCase(TestCase):

    def test_select_invalid_fields(self):
        with self.assertRaises(FieldError) as exception:
            class ThisShouldFail(ModelReporter):
                class Meta:
                    model = Permission
                    fields = ('foo', 'span', 'codename')

        self.assertEqual(
            exception.exception.message,
            'Unknown field(s) (foo, span) specified for Permission'
        )

    def test_invalid_headers(self):
        with self.assertRaises(FieldError) as exception:
            class ThisShouldFail(ModelReporter):
                class Meta:
                    model = Permission
                    custom_headers = {
                        'foo': 'Foo', 'span': 'Span', 'codename': 'Meh'
                    }

        self.assertEqual(
            exception.exception.message,
            'Unknown header(s) (foo, span) specified for Permission'
        )

    def test_custom_header_with_non_selected_field(self):
        with self.assertRaises(FieldError) as exception:
            class ThisShouldFail(ModelReporter):
                class Meta:
                    model = Permission
                    fields = ('name',)
                    custom_headers = {'codename': 'Meh'}

        self.assertEqual(
            exception.exception.message,
            'Unknown header(s) (codename) specified for Permission'
        )


# Test classes
class BaseUserReporter(ModelReporter):
    class Meta:
        model = get_user_model()


class PermissionReporterWithAllFields(ModelReporter):
    class Meta:
        model = Permission


class PermissionReporterWithSomeFields(ModelReporter):
    class Meta:
        model = Permission
        fields = ('name', 'codename')


class PermissionReporterWithSomeFieldsAndCustomRenderer(ModelReporter):
    class Meta:
        model = Permission
        fields = ('name', 'codename')

    def render_codename(self, instance):
        return instance.codename.replace('_', ' ').capitalize()


class PermissionReporterWithCustomHeaders(ModelReporter):
    class Meta:
        model = Permission
        custom_headers = {
            'id': 'Key',
            'name': 'Foo',
        }


class GroupReporter(ModelReporter):
    class Meta:
        model = Group
        fields = ('name', 'permissions',)


class ModelReporterTestCase(TestCase):

    def _create_users(self, _quantity=5):
        for i in range(1, _quantity + 1):
            username = 'foo%s' % i
            email = '%s@example.com' % i

            get_user_model().objects.create(username=username, email=email)

    def test_basic_reporter(self):
        reporter = BaseUserReporter()

        self.assertEqual(reporter.items.count(), 0)

    def test_reporter_with_some_items(self):
        self._create_users(_quantity=5)
        reporter = BaseUserReporter()

        self.assertEqual(reporter.items.count(), 5)

    def test_reporter_with_fixed_queryset(self):
        self._create_users(_quantity=10)
        reporter = BaseUserReporter(get_user_model().objects.all()[:7])

        self.assertEqual(reporter.items.count(), 7)

    def test_reporter_gets_all_model_fields(self):
        reporter = PermissionReporterWithAllFields()

        self.assertEqual(
            set(reporter.fields),
            set(['codename', 'content_type', 'group', u'id', 'name', 'user'])
        )

    def test_reporter_gets_given_model_fields(self):
        reporter = PermissionReporterWithSomeFields()

        self.assertEqual(
            reporter.fields,
            ('name', 'codename')
        )

    def test_default_headers(self):
        reporter = PermissionReporterWithAllFields()

        self.assertEqual(
            set(reporter.rendered_headers()),
            set([u'Codename', u'Content type', 'Group', u'Id', u'Name', 'User'])
        )

    def test_custom_headers(self):
        reporter = PermissionReporterWithCustomHeaders()

        self.assertEqual(
            set(reporter.rendered_headers()),
            set([u'Codename', u'Content type', 'Group', u'Key', u'Foo', 'User'])
        )

    def test_row_generation_with_all_fields(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        reporter = PermissionReporterWithAllFields(permissions)
        permission = permissions.get(codename='add_permission')

        self.assertEqual(
            reporter.rendered_fields(permission),
            {
                'codename': u'add_permission', 'content_type': u'permission',
                'group': u'', u'id': u'1',
                'name': u'Can add permission', 'user': u'',
            }
        )

    def test_generate_all_rows_with_all_fields(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        reporter = PermissionReporterWithAllFields(permissions)

        self.assertEqual(
            [row for row in reporter.rendered_rows()],
            [
                [u'add_permission', u'permission', u'', u'1', u'Can add permission', u''],
                [u'change_permission', u'permission', u'', u'2', u'Can change permission', u''],
                [u'delete_permission', u'permission', u'', u'3', u'Can delete permission', u''],
            ]
        )

    def test_row_generation_with_some_fields(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        reporter = PermissionReporterWithSomeFields(permissions)
        permission = permissions.get(codename='add_permission')

        self.assertEqual(
            reporter.rendered_fields(permission),
            {'codename': 'add_permission', 'name': 'Can add permission'}
        )

    def test_generate_all_rows_with_some_fields(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        reporter = PermissionReporterWithSomeFields(permissions)

        self.assertEqual(
            [row for row in reporter.rendered_rows()],
            [
                ['Can add permission', 'add_permission'],
                ['Can change permission', 'change_permission'],
                ['Can delete permission', 'delete_permission'],
            ]
        )

    def test_many_to_many_fields(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        self.assertEqual(Group.objects.count(), 0)
        group = Group.objects.create(name='foo')
        group.permissions.add(*permissions)

        reporter = GroupReporter()

        self.assertEqual(
            [row for row in reporter.rendered_rows()],
            [
                [u'foo', u'auth | permission | Can add permission, auth | permission | Can change permission, auth | permission | Can delete permission'],
            ]
        )

    def test_custom_renderer(self):
        ct = ContentType.objects.get_for_model(Permission)
        permissions = Permission.objects.filter(content_type=ct)

        reporter = PermissionReporterWithSomeFieldsAndCustomRenderer(permissions)

        self.assertEqual(
            [row for row in reporter.rendered_rows()],
            [
                ['Can add permission', 'Add permission'],
                ['Can change permission', 'Change permission'],
                ['Can delete permission', 'Delete permission'],
            ]
        )
