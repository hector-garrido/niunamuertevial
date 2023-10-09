import numpy as np
import requests
import lxml.html as html
from bs4 import BeautifulSoup


def get_soup(url):

    try:

        response = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
        try:
            home = response.content.decode("utf-8")
        except:
            home = response.content.decode("latin1")
        soup = BeautifulSoup(home, "html.parser")
        return soup, response.status_code

    except requests.exceptions.Timeout as err:
        print("timeout :(")
        return 1, 1

    except:
        return 1, 1


def get_clean_text(input):

    clean_text = input.copy()

    clean_text = clean_text.str.lower()

    clean_text = (
        clean_text.str.replace(".", "")
        .str.replace(":", "")
        .str.replace(";", "")
        .str.replace(",", "")
        .str.replace("-", "")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
        .str.replace("  ", " ")
    )

    return clean_text


def get_edad(input, i):

    if len(np.where(np.array(input[i]) == "años")[0]) > 0:
        edad_position = np.where(np.array(input[i]) == "años")[0][0] - 1

        return input[i][edad_position]
