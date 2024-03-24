import glob
import json
import logging
import os
import random
import sys
import time
from typing import List

import helium as he
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)


def expand_search_terms(search_terms: str) -> List[str]:
    """Use OpenAI API to expand search terms."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = """
        Input: search_terms
        Output:: Provide the search terms in a JSON format, with the keys being the numbers 1 to 10 and the values being the corresponding search terms.
          Ensure that the search terms are closely related to the initial input but vary in their phrasing and word choice to capture a wide range of relevant searches.
        Example:
        Input: Chinese name seals
        Output:
        {
        '1': 'Chinese name seals',
        '2': 'Chinese chops',
        '3': 'Hanko seals',
        '4': 'Chinese seal carving',
        '5': 'Chinese signature stamps',
        '6': 'Asian name seals',
        '7': 'Chinese calligraphy seals',
        '8': 'Traditional Chinese seals',
        '9': 'Chinese seal engraving',
        '10': 'Chinese name stamps'
        }
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Expand search terms for {search_terms}"},
        ],
    )
    assistant_message = response.choices[0].message.content
    search_terms_json = json.loads(assistant_message.replace("'", '"'))
    expanded_terms = list(search_terms_json.values())
    return expanded_terms


def start_chrome_and_login():
    email = os.getenv("ETSYHUNT_EMAIL")
    pwd = os.getenv("ETSYHUNT_PWD")
    if not email or not pwd:
        logging.error("Please provide email and password in .env file!")
        sys.exit(1)
    he.start_chrome("https://etsyhunt.com/user/login")
    he.click(he.TextField("Please enter your email"))
    he.write(email)
    he.click(he.TextField("Please enter your password"))
    he.write(pwd)
    he.click("Login")
    he.wait_until(he.Text("Dashboard").exists)
    # Random sleep to avoid detection
    time.sleep(random.randint(1, 3))


def search_for_product(search_term):
    logging.info("Searching for product: %s", search_term)
    he.click("Find Hot Product")
    he.click(he.TextField())
    he.wait_until(he.Button("Search").exists)
    try:
        time.sleep(random.randint(3, 5))
        he.write(search_term)
        he.press(he.click(he.Button("Search")))
    except TypeError:
        pass


def download_and_rename_csv(search_term):
    if he.Text("Compose your reply").exists():
        he.click(he.Text("Compose your reply"))

    if he.Button("close chat").exists():
        he.click(he.Button("close chat"))

    logging.info("Downloading CSV file for %s", search_term)
    he.wait_until(he.Text("Export to CSV").exists)
    time.sleep(random.randint(1, 3))
    he.click(he.Text("Export to CSV"))
    he.click(he.Text("All Page"))
    time.sleep(3)
    downloads_folder = os.path.expanduser("~/Downloads")
    csv_file = glob.glob(os.path.join(downloads_folder, "product_detail_*.csv"))[0]
    new_path = os.path.join(downloads_folder, f"{search_term}_product_detail.csv")
    if os.path.exists(csv_file):
        logging.info("Renaming file to: %s", new_path)
        os.rename(csv_file, new_path)
    else:
        logging.warning("No CSV file found!")


def main(search_term):
    start_chrome_and_login()
    logging.info("Logged in successfully!")
    search_for_product(search_term)
    download_and_rename_csv(search_term)


def usage():
    logging.error("Usage: python etsyhunt_bot.py <search terms>")
    sys.exit(1)


if __name__ == "__main__":
    search_terms = " ".join(sys.argv[1:])
    if not search_terms:
        usage()
    main(search_terms)
