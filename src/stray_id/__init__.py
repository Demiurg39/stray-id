# __init__.py -- entry point of the project

import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")

def main() -> None:
    print("Hello from stray-id!")
    print(f"Bot token: {TOKEN}")

if __name__ == "__main__":
    main()
