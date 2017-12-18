from setuptools import setup

setup(name='settler',
      version='0.1',
      description='Make a fresh OS install feel like home!',
      url='http://github.com/dulex123/settler',
      author='Dusan Josipovic',
      author_email='dusanix@gmail.com',
      license='MIT',
      packages=['settler'],
      zip_safe=False,
      scripts=['bin/settler'],
      install_requires=[
        'Click',
        ]
      )
