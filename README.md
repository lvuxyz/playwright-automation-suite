# Playwright Automation Suite

A collection of Python + Playwright desktop automation tools built with Tkinter.

## Projects

### [`auto_change_password`](./auto_change_password/README.md)
Batch password-change automation for web accounts.  
Supports importing account lists from **CSV**, **Excel**, and **TXT** files, then automates login and password-change flows through a Chromium browser using Playwright.

### [`auto_web_ghost`](./auto_web_ghost/README.md)
Generic Playwright web-flow automation tool.  
Navigates to a target URL, performs configurable login/interaction steps, and captures screenshots — useful for smoke-testing or scripting repetitive browser tasks.

## Requirements

- Python 3.10+
- [Playwright](https://playwright.dev/python/) (`pip install playwright && playwright install chromium`)
- See each sub-project's `requirements.txt` for full dependencies.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/lvuxyz/playwright-automation-suite.git
cd playwright-automation-suite

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies for a sub-project
pip install -r auto_change_password/requirements.txt
playwright install chromium

# Copy and edit the config
copy auto_change_password\config.example.py auto_change_password\config.py

# Run
python auto_change_password/main.py
```

## License

MIT
