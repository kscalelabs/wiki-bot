"""Defines common constants and functions."""

import os

SITE_ROOT = "humanoids.wiki"


def get_openai_key() -> str:
    if "WIKIBOT_OPENAI_API_KEY" not in os.environ:
        raise ValueError("OpenAI API key not found in environment variables.")
    return os.environ["WIKIBOT_OPENAI_API_KEY"]


def get_tavily_key() -> str:
    if "WIKIBOT_TAVILY_API_KEY" not in os.environ:
        raise ValueError("Tavily API key not found in environment variables.")
    return os.environ["WIKIBOT_TAVILY_API_KEY"]


def get_username() -> str:
    if "WIKIBOT_USERNAME" not in os.environ:
        raise ValueError("Username not found in environment variables.")
    return os.environ["WIKIBOT_USERNAME"]


def get_password() -> str:
    if "WIKIBOT_PASSWORD" not in os.environ:
        raise ValueError("Password not found in environment variables.")
    return os.environ["WIKIBOT_PASSWORD"]
