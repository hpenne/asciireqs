from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.adoc').read_text(encoding='utf-8')

setup(
    name="asciireqs",
    version='0.0.2',
    description='A simple text-based Requirement Management System using asciidoc',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # url='https://github.com/pypa/sampleproject',
    author='Helge Penne',
    # author_email='author@example.com',
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        # 'Intended Audience :: Developers',
        # 'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: 3.10",
        'Programming Language :: Python :: 3 :: Only',
    ],
    # keywords='sample, setuptools, development',  # Optional
    packages=find_packages(),
    python_requires='>=3.7, <4',
    install_requires=[
        "PyYAML",
        "openpyxl"
    ],
    entry_points={  # Optional
        'console_scripts': [
            'asciireq=asciireqs.asciireq:main',
            'asciireqexport=asciireqs.asciireqexport:main'
        ],
    }
)
