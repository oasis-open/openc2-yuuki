from distutils.core import setup

setup(name='yuuki',
      version='0.1a4',
      description='OpenC2 proxy',
      author='Joshua Brule',
      author_email='jtcbrule@gmail.com',
      packages=['yuuki'],
      install_requires=[
          "requests >= 2.22.0",
          "PyYAML >= 5.1",
          "Flask >= 1.0.3"])


