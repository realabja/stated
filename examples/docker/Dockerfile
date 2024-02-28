from python:3.12

RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="$PATH:/root/.local/bin"
RUN poetry config virtualenvs.create false
RUN poetry --version
WORKDIR /app
COPY fastapi/pyproject.toml fastapi/poetry.lock /app/
RUN poetry install
