import os
from setuptools import setup


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(
    name="django-reportato",
    version="1.0",
    author="Pablo Recio",
    author_email="pablo@potatolondon.com",
    description="Very simple CSV reports with Django",
    long_description=(read('README.md')),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    license="BSD",
    keywords="django reports potato csv",
    url='https://github.com/potatolondon/reportato',
    packages=['reportato'],
    zip_safe=False,
)
