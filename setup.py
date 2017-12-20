from setuptools import setup

setup(name='settler',
      version='0.1',
      description='Make a fresh OS install feel like home!',
      url='http://github.com/dulex123/settler',
      author='Dusan Josipovic',
      author_email='dusanix@gmail.com',
      license='MIT',
      download_url = 'https://github.com/dulex123/settler/archive/0.1.tar.gz',
      packages=['settler'],
      keywords=['dotfiles', 'settler', 'setup'],
      zip_safe=False,
      scripts=['bin/settler'],
      install_requires=[
        'Click>=6.0',
        'GitPython>=2.0'
        ]
      )
