"""Updates an article on the wiki.

This action queries the "Stompy, Expand!" category, finds all articles in it,
and expands on them by calling ChatGPT. The expanded text is then added to the
article.
"""

import argparse
import asyncio
import json
import logging

import mwclient
from openai import AsyncOpenAI
from tavily import TavilyClient

from wikibot.common import ASSISTANT_ID, SITE_ROOT, get_openai_key, get_password, get_tavily_key, get_username
from wikibot.logging import configure_logging

logger = logging.getLogger(__name__)


async def expand_content_with_gpt(text: str) -> str:
    openai_client = AsyncOpenAI(api_key=get_openai_key())
    tavily_client = TavilyClient(api_key=get_tavily_key())

    # Creates a new thread with the text as the user message.
    thread = await openai_client.beta.threads.create()
    await openai_client.beta.threads.messages.create(thread_id=thread.id, role="user", content=text)

    run = await openai_client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=ASSISTANT_ID)

    while True:
        if run.status == "failed":
            raise ValueError("Failed to expand content")

        if run.status == "completed":
            break

        # Gets the search query.
        logger.info("Handling action")
        if (action := run.required_action) is None:
            raise ValueError("Run requires action")

        tool_outputs = []
        for tool_call in action.submit_tool_outputs.tool_calls:
            params = json.loads(tool_call.function.arguments)
            query = params["query"]
            search_results = tavily_client.search(query)
            if not search_results:
                raise ValueError("No search results found")
            tool_outputs.append({"output": json.dumps(search_results), "tool_call_id": tool_call.id})

        # Sends the search results to the assistant.
        await openai_client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs,  # type: ignore[arg-type]
        )

        # Polls the run.
        run = await openai_client.beta.threads.runs.poll(thread_id=thread.id, run_id=run.id)

    # Gets the last message from the assistant.
    messages = await openai_client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    text_content = next(c for d in messages.data if d.assistant_id is not None for c in d.content if c.type == "text")
    return text_content.text.value


async def main() -> None:
    parser = argparse.ArgumentParser(description="Update articles on the wiki.")
    parser.add_argument("-c", "--category", type=str, default="Stompy, Expand!", help="The category to update.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("-o", "--one", action="store_true", help="Only update one article.")
    parser.add_argument("-a", "--accept", action="store_true", help="Prompts the user to accept the changes.")
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
        expanded_content = await expand_content_with_gpt(content)
        if args.accept:
            logger.info("Expanded content:\n%s", expanded_content)
            if input("Accept changes? (y/n): ").strip().lower() != "y":
                logger.info("Changes not accepted, skipping page")
                continue
        else:
            logger.debug("Expanded content:\n%s", expanded_content)

        # Updates the page with the expanded content.
        page.save(expanded_content, summary="Bot expanded article")
        logger.info("Updated page %s", page.name)

        if args.one:
            break


if __name__ == "__main__":
    # python -m wikibot.update_article
    asyncio.run(main())
