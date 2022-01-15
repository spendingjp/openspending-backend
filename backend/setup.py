import os

from setuptools import setup

setup(
    name="wdmmgserver",
    version="0.0.1",
    author="spendingjp contributers",
    author_email="osoken@outlook.jp",
    license="MIT",
    url="https://github.com/spendingjp/openspending-backend",
    description="Where does my money go? data handler",
    long_description="Where does my money go? data handler",
    packages=["wdmmgserver"],
    install_requires=[
        "django",
        "python-dotenv",
        "django-shortuuidfield",
        "djangorestframework",
        "django-filter",
        "djangorestframework-camel-case",
        "pykakasi",
        "drf-nested-routers",
        "django-polymorphic",
    ],
    extras_require={"dev": ["flake8", "black", "isort", "psycopg2-binary"], "prod": ["psycopg2"]},
)
