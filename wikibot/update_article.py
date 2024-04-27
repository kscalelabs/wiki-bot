"""Updates an article on the wiki.

This action queries the "Stompy, Expand!" category, finds all articles in it,
and expands on them by calling ChatGPT. The expanded text is then added to the
article.
"""

import argparse
import logging

import mwclient
from openai import OpenAI

from wikibot.common import SITE_ROOT, get_openai_key, get_password, get_username
from wikibot.logging import configure_logging

logger = logging.getLogger(__name__)

PROMPT = """
You are a bot tasked with maintaining a public wiki about humanoid robots. Users will give you articles to expand upon,
and you will use your knowledge and search capabilities to provide accurate and informative expanded content in the
style of a typical Wikipedia article, with high-quality citations for references.

Our wiki has three main infoboxes that we use:

{{infobox company
| name =
| country =
| website_link =
| robots =
}}

{{infobox robot
| name =
| organization =
| video_link =
| cost =
| height =
| weight =
| speed =
| lift_force =
| battery_life =
| battery_capacity =
| purchase_link =
| number_made =
| dof =
| status =
}}

{{infobox actuator
| name =
| manufacturer =
| cost =
| purchase_link =
| nominal_torque =
| peak_torque =
| weight =
| dimensions =
| gear_ratio =
| voltage =
| cad_link =
| interface =
| gear_type =
}}

In the above infoboxes, any field that ends with "link" should be a raw URL.

Conform to the formatting guidelines below when writing articles. Specifically, DO NOT mistakenly use Markdown
formatting in the article - instead, use vanilla MediaWiki syntax.

- Use `== Headings ==` for section headings.
- Use `=== Subheadings ===` for subsection headings.
- Use bullet points for lists, delineated by `*`, `**`, `***`, etc.
- Use numbered lists for ordered lists, delineated by `#`, `##`, `###`, etc.
- Use `''Italic text''` for italics.
- Use `'''Bold text'''` for bold.
- Use `'''''Bold and italic'''''` for bold and italic.
- Use `[[Link]]` for internal links.
- Use `[[Link|Text]]` for piped links.
- Use `<ref>Reference</ref>` for references.
- Use `<ref name="Name">Reference</ref>` for named references.
- Use `<references />` for the references section.
- Do not use any other templates besides the infoboxes mentioned above.

Please write these articles with the following guidelines in mind:

- Write from a neutral, purely factual point of view.
- Use proper grammar and spelling.
- Provide accurate and up-to-date information, with lots of citations.
- Make sure the article is well-organized and easy to read.
- Use correct MediaWiki syntax for formatting.
- Use links to other articles in the wiki where appropriate.
- Do not add any additional media to the article, but keep any existing media.
- Avoid adding raw links to the article. Instead, use proper citations. However, only use raw URLs for the infoboxes.
- For citations, create a "References" section at the end of the article.
""".strip()


def expand_content_with_gpt(text: str, model: str) -> str:
    client = OpenAI(api_key=get_openai_key())
    user_prompt = f"Rewrite the following article to be more complete:\n\n```\n{text}\n```"
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    if (content := completion.choices[0].message.content) is None:
        raise ValueError("Failed to expand content")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Update articles on the wiki.")
    parser.add_argument("-c", "--category", type=str, default="Stompy, Expand!", help="The category to update.")
    parser.add_argument("-m", "--model", type=str, default="gpt-4-turbo", help="The OpenAI model to use.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("-o", "--one", action="store_true", help="Only update one article.")
    args = parser.parse_args()

    configure_logging(level=logging.DEBUG if args.debug else logging.INFO)

    # Authenticates the bot.
    username = get_username()
    password = get_password()
    site = mwclient.Site(SITE_ROOT, path="/")
    site.login(username, password)

    # Fetches all pages in the category.
    category = site.Categories[args.category]

    for page in category:
        logger.info("Expanding page %s", page.name)

        # Fetches the current content of the page.
        content = page.text()
        logger.debug("Original content:\n%s", content)

        # Removes the category tag.
        for c in (args.category, f" {args.category}"):
            content = content.replace(c, "")
        content = content.strip()

        # Expands the content with GPT.
        expanded_content = expand_content_with_gpt(content, args.model)
        logger.debug("Expanded content:\n%s", expanded_content)

        # Updates the page with the expanded content.
        page.save(expanded_content, summary="Bot expanded article")
        logger.info("Updated page %s", page.name)

        if args.one:
            break


if __name__ == "__main__":
    # python -m wikibot.update_article
    main()
