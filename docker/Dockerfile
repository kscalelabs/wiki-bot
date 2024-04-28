# Dockerfile for the FastAPI application.

FROM public.ecr.aws/lambda/python:3.11

WORKDIR /app

# Installs Pip for Python 3.11.
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.11 get-pip.py && \
    rm get-pip.py

# Copies over and installs requirements file first.
COPY wikibot/requirements.txt .
RUN pip install -r requirements.txt

# Installs the package.
RUN pip install '.'

# Command to run to update the article.
CMD ["wikibot.update_article.lambda_handler"]
