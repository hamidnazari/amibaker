from setuptools import setup
from amibaker.version import VERSION

setup(
    name='amibaker',
    version=VERSION,
    description='Automate creation of AWS AMIs.',
    long_description='This tool creates temporary hosts, allows temporary ' +
    'access, provisions it, creates an image from it, configures the ' +
    'image, cleans up, and give you an AMI ID.',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 4 - Beta',
    ],
    keywords=[
        'aws',
        'amazon web services',
        'ami',
        'amazon machine images',
        'automation',
    ],
    author='Hamid Nazari',
    author_email='hn@linux.com',
    maintainer='Hamid Nazari',
    maintainer_email='hn@linux.com',
    url='http://github.com/hamidnazari/amibaker',
    license='MIT',
    packages=['amibaker'],
    entry_points={
        'console_scripts': [
            'amibaker = amibaker.main:main',
        ],
    },
    install_requires=[
        'awsclpy==0.3.5',
        'Fabric==1.10.2',
        'Jinja2==2.7.3',
        'PyYAML==3.11'
    ],
    zip_safe=False)
