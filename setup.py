import pip
from setuptools import setup
from pip.req import parse_requirements
from amibaker.version import VERSION

install_reqs = parse_requirements("./requirements.txt",
                                  session=pip.download.PipSession())
reqs = [str(ir.req) for ir in install_reqs]

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
    install_requires=reqs,
    zip_safe=False)
