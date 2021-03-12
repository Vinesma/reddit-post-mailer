from setuptools import setup
from setuptools import find_packages

with open("./README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="redditmailer",
    description="Find the most upvoted reddit posts and send an email with the contents to the user.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="3.0.2",
    url="https://github.com/Vinesma/reddit-post-mailer",
    author="Otavio Cornelio",
    author_email="vinesma.work@gmail.com",
    license="MIT",
    scripts=["scripts/redditmailer"],
    packages=find_packages("src"),
    package_dir={'': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    install_requires=["yagmail"]
)
