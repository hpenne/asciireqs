from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "long-description.md").read_text(encoding="utf-8")

setup(
    name="asciireqs",
    version="0.0.7",
    description="Text-based Requirement Management using AsciiDoc and version control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url='https://github.com/pypa/sampleproject',
    author="Helge Penne",
    author_email='hpenne@gmail.com',
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        "Topic :: Documentation",
        "Topic :: Utilities",
        "Topic :: Text Processing :: Markup",
        "Topic :: Software Development :: Documentation",

        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords='Requirement Management, version control, git, text-based, AsciiDoc',
    packages=find_packages(),
    python_requires=">=3.7, <4",
    install_requires=["PyYAML", "openpyxl"],
    entry_points={  # Optional
        "console_scripts": [
            "asciireq=asciireqs.asciireq:main",
            "asciireqexport=asciireqs.asciireqexport:main",
        ],
    },
)
