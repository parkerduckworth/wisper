from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='wisper',
      version='1.0.0',
      description='Encrypted IRC',
      long_description=readme(),
      url='https://github.com/parkerduckworth/wisper',
      author='parkerduckworth',
      author_email='parkerduckworth@gmail.com',
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            'Topic :: Communications :: Chat :: Internet Relay Chat',
            'Environment :: Console',
            'Intended Audience :: End Users/Desktop',
            'Operating System :: POSIX'
      ],
      license='MIT',
      packages=find_packages(),
      entry_points={
            'console_scripts': ['wisper-runserver=wisper.session:run_server',
                                'wisper=wisper.session:run_client']
      },
      install_requires=[
            'boto3',
            'cryptography',
            'protobuf',
            'psutil',
            'requests',
            'werkzeug'
      ],
      zip_safe=False)
