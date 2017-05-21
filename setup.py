import os
from setuptools import setup, find_packages


version = '0.1.2'
README = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = open(README).read()
setup(
    name='sqlalchemy_zdb',
    version=version,
    description='SQLAlchemy support for ZomboDB',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3'
    ],
    keywords='sqlalchemy zombodb',
    author='xxxbobrxxx, Sander Ferdinand',
    author_email='xxxbobrxxx@gmail.com, sa.ferdinand@gmail.com',
    url='https://github.com/skftn/sqlalchemy_zdb',
    install_requires=[
        'sqlalchemy>=1.1.6',
        'sqlalchemy_utils',
        'psycopg2'
    ],
    download_url=
        'https://github.com/skftn/sqlalchemy_zdb/archive/master.zip',
    packages=find_packages(),
    include_package_data=True,
)
