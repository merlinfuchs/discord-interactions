
import pathlib
import re

import setuptools

ROOT = pathlib.Path(__file__).parent

with open(ROOT / "README.md", "r") as f:
    long_description = f.read()


with open(ROOT / "dc_interactions" / "__init__.py", encoding="utf-8") as f:
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not parse version.")
    VERSION = match.group(1)

with open(ROOT / "requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="dc_interactions",
    version=VERSION,
    author="Merlin Fuchs",
    author_email="contact@merlin.gg",
    description="An async implementation of discord interactions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/merlinfuchs/discord-interactions",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    python_requires=">=3.6",
)