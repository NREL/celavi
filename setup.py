import setuptools

name = 'tinylca'
version = '0.0.1'

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name=name,
    version=version,
    author='Alicia Key',
    author_email='alicia.key@nrel.gov',
    description='Experiments in LCA modeling',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['tinylca'],
    test_suite='nose.collector',
    tests_require=['nose'],
    install_requires=[
        'pandas',
        'numpy',
        'openmdao'
    ],
    command_options={
            'build_sphinx': {
                'project': ('setup.py', name),
                'version': ('setup.py', version),
                # 'release': ('setup.py', release),  # Not yet needed
                'source_dir': ('setup.py', 'docs')}}
)
