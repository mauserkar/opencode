FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin mcp

WORKDIR /app

COPY mcp-jira/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ira.py ./jira.py
COPY server.py ./server.py

USER mcp

ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
