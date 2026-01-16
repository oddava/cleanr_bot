FROM python:3.12-slim-bookworm

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependencies first to reuse cache
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

# Run the bot
CMD ["uv", "run", "python", "bot.py"]
