import os
from bs4 import BeautifulSoup
import requests
import lxml.html as html
import pandas as pd
import re
import numpy as np
from aux_functions import get_soup, get_clean_text, get_edad
from time import time

INPUT_FILE_PATH = "input_urls.xlsx"
OUTPUT_FILE_PATH = "output_data.csv"
take_sample = True
sample_size = 500

################################################################################
#   read and process dataset

start = time()

df = pd.read_excel(INPUT_FILE_PATH)
# df = pd.read_csv(INPUT_FILE_PATH, header=1)

df["aux"] = df["URL noticia"].copy()
df["aux"] = df["aux"].str.replace("http://", "")
df["aux"] = df["aux"].str.replace("https://", "")

aux_sitio_1 = df.loc[df.aux.notnull(), "aux"].str.split("/")
aux_sitio_2 = [x[0] for x in aux_sitio_1]
df["sitio"] = ""
df.loc[df.aux.notnull(), "sitio"] = [x for x in aux_sitio_2]
del aux_sitio_1, aux_sitio_2

df["milenio_dummy"] = df.sitio == "www.milenio.com"
df["elsol_dummy"] = df.sitio.str.contains("elsolde", case=False)

# if the url list is too big, you can take the first n rows for a test instead of the whole dataset
if take_sample:
    df = df.head(sample_size)

aux_url_split_1 = df.loc[df["URL noticia"].notnull(), "URL noticia"].str.split(" y ")
aux_url_split_2 = [x[0] for x in aux_url_split_1]
df["url_0"] = np.nan
df.loc[df["URL noticia"].notnull(), "url_0"] = aux_url_split_2
del aux_url_split_1, aux_url_split_2

df["texto"] = ""
df["tags"] = ""
df["status_code"] = ""

################################################################################
#   get text milenio

k = 0
for i in df[df.milenio_dummy].index:
    k += 1

    url = df["url_0"][i]
    soup, status_code = get_soup(url)

    # add title
    texto = soup.find_all("title")[0].text

    # add body
    for x in soup.find_all("p"):
        texto += " "
        texto += x.text

    df.loc[i, "texto"] = texto

    if k % 50 == 0:
        print(f"{k} de {len(df[df.milenio_dummy].index)} completados")

print("milenio completado")

################################################################################
#   get text elsol

k = 0
for i in df[df.elsol_dummy].index:
    k += 1

    url = df["url_0"][i]
    soup, status_code = get_soup(url)

    try:
        # add title
        texto = soup.find_all("title")[0].text
        texto += " "

        # add subtitle
        texto += soup.find(class_="subtitle").text
        texto += " "

        # add tags
        gtm = soup.find_all("script")
        for x in gtm:
            if 'dataLayer.push({"tags"' in x.text:
                gtm_tags = re.search("\$\[.*\]", x.text).group()
                gtm_tags = gtm_tags[2:-1]
                break
        df.loc[i, "tags"] = gtm_tags

        # add body

        try:
            body_texts = soup.find(class_="content-body clearfix").find_all(
                "p", class_=None
            )
            for x in body_texts:
                if len(x.findChildren()) < 10:
                    texto += x.text
                    texto += " "
        except:
            body_texts = soup.find_all("p")
            for x in body_texts:
                texto += x.text
                texto += " "

        try:
            body_texts_cont = soup.find(
                class_="content-continued-body clearfix"
            ).find_all("p", class_=None)
            if body_texts_cont != body_texts:
                for x in body_texts_cont:
                    if len(x.findChildren()) < 10:
                        texto += x.text
                        texto += " "
        except:
            1

        df.loc[i, "texto"] = texto

    except:
        1

    df.loc[i, "status_code"] = status_code

    if k % 50 == 0:
        print(f"{k} de {len(df[df.elsol_dummy].index)} completados")

print("elsol completado")

################################################################################
#   get text for the other sites (unstructured)

k = 0
for i in df[~df.elsol_dummy & ~df.milenio_dummy].index:
    k += 1

    url = df["url_0"][i]
    soup, status_code = get_soup(url)
    if soup != 1:

        try:
            # add title
            texto = soup.find_all("title")[0].text
            texto += " "

            # add subtitle
            texto += soup.find(class_="subtitle").text
            texto += " "

        except:
            texto = ""

        # add body
        try:
            aux = soup.find_all("p")
            for x in aux:
                texto += x.text
                texto += " "
            df.loc[i, "texto"] = texto

        except:
            1

    else:
        1

        df.loc[i, "status_code"] = status_code

    if k % 50 == 0:
        print(
            f"{k} de {len(df[~df.elsol_dummy & ~df.milenio_dummy].index)} completados"
        )

print("el resto completado")


################################################################################
#   process to get features from the text

df["tags"] = df["tags"].str.lower()

df["texto_limpio"] = get_clean_text(df["texto"])

df["texto_lista"] = df.texto_limpio.str.split(" ")

df.loc[df.texto_limpio.isnull(), "texto_limpio"] = ""

df["URL noticia 0"] = df["URL noticia"].copy()
df.loc[df["URL noticia"].isnull(), "URL noticia 0"] = ""

df["edad"] = np.nan
for i in df.index:
    df.loc[i, "edad"] = get_edad(df.texto_lista, i)

################################################################################
#   classification of cases by medium of transport of the victim

df["modo"] = "peaton"

mask_bici = df.texto_limpio.str.contains("cicl[ei]", case=False, regex=True)
df.loc[mask_bici, "modo"] = "bici"

mask_moto_1 = df.texto_limpio.str.contains("moto[^r]", case=False, regex=True)
mask_moto_2 = ~df["URL noticia 0"].str.contains(
    "por-moto|por-una-moto", case=False, regex=True
)
df.loc[(mask_moto_1) & (mask_moto_2), "modo"] = "moto"

si_moto = ["-a-moto", "motociclista-tras", "motocilcista-al"]
for x in si_moto:
    aux_mask_moto = df["URL noticia 0"].str.contains(x, case=False, regex=True)
    df.loc[aux_mask_moto, "modo"] = "moto"

mask_nothing = df.texto_limpio == ""
df.loc[mask_nothing, "modo"] = ""

################################################################################
#   export output to file

df.milenio_dummy *= 1
df.elsol_dummy *= 1

df = df.drop(columns=["aux", "url_0", "texto_limpio", "URL noticia 0", "texto_lista"])

try:
    df.to_csv(OUTPUT_FILE_PATH, index=False)
except:
    df.to_csv(OUTPUT_FILE_PATH, index=False, encoding="latin1", errors="ignore")

print("Hecho! en", (time() - start) / 60, "min")
