    # Sync dependencies from lockfile
    uv sync
    # Add a new package
    uv add <PACKAGE-NAME>
    # Run Python files
    uv run python <PYTHON-FILE>

    #commit with suitable message. The message should be bullet point style, simple, and concise.
    git commit -m "<MESSAGE>"

    # LIBRARY VERSIONING
    1. Always check `package.json`, `pyproject.toml`, or `mix.exs` first to find installed versions.
    2. If the version is very new (released in late 2024/2025) or if you are unsure about breaking changes, USE `context7` to fetch the documentation.
    3. Do not guess on major version upgrades (e.g., Python 3.12 -> 3.13, Tailwind 3 -> 4).

    # TOOL USAGE RULES
    Always use the `context7` tool when I ask for code generation, setup steps, or library documentation.
    - You do NOT need to ask for permission.
    - If I mention a library (e.g., "Airflow", "Next.js"), automatically use `context7` to find the latest docs for it.
    - If you are unsure which version I am using, use `context7` to check the latest stable version.
    - When you tried twice to fix an error and still can't fix it, use the context7 tool to find the solution.

    # For md files
    - Don't use convoluted language. e.g., 
        - saving massive amounts of bandwidth -> saving bandwidth
        - powerful tools -> tools
    - No need to use analogies or metaphors unless asked to.
    