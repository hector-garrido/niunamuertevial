import os
from bs4 import BeautifulSoup
import requests
import lxml.html as html
import pandas as pd
import re
import numpy as np
from aux_functions import get_soup, get_clean_text, get_edad
from time import time
from search import search_query, _search_query

OUTPUT_FILE_PATH = "output_data.csv"
EXCEL_CHAR_LIMIT = 32700

################################################################################
#   get urls

start = time()

token = os.getenv("APIFY_TOKEN")

has_url_file = input("¿Cuentas con un archivo excel con urls? y/n: ")

if has_url_file == "y":
    input_file_path = input("Introduce el nombre del archivo excel: ")
    df = pd.read_excel(input_file_path)

elif has_url_file == "n":

    print(
        "Procediendo a realizar scraping de urls por medio de Apify (requiere token)..."
    )

    if token is None:
        print(
            "Por favor establece la variable de entorno APIFY_TOKEN y ejecuta de nuevo el comando"
        )
        exit(1)

    has_query = input("¿Tienes una query personalizada? y/n: ")
    if has_query == "y":
        query = input("Introduce tu query: ")
    elif has_query == "n":
        # ignore urls to pdfs sicne their extraction yields weird stuff
        query = "(atropella OR atropellada OR atropellados OR atropelladas OR atropellado OR arrollado OR arrollada OR arrolla OR embiste) AND \
            (muerte OR muerto OR muerta OR muere OR murió OR fallecido OR fallecida OR fallece OR falleció OR perece OR pereció OR cuerpo OR cadáver OR fatal OR mortal OR mata) \
            -site:sv -site:es -site:cl -site:pe -site:ar -site:co -site:hn \
            -filetype:pdf "#\
            # after:2024-08-25 before:2024-08-26"
    else:
        print("Comando desconocido. Interrumpiendo programa.")
        exit(1)

    print(f"Using query: {query}")
    results = search_query(query, token)

    df = pd.DataFrame(
        {
            "url": [x.url for x in results],
            "date": [x.date for x in results],
            "keywords": [x.keywords for x in results],
        }
    )

    print("Scraping de urls completado.")

else:
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

################################################################################
# process data

df = df.rename(columns={"url": "URL noticia"})

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
print(f"Tamaño: {df.shape[0]}")
take_sample = input("¿Quieres ocupar solo una muestra de los datos? y/n: ")

if take_sample == "y":
    sample_size = input("Indica el tamaño de la muestra: ")
    try:
        sample_size = int(sample_size)
        df = df.head(sample_size)
    except Exception as e:
        print(e)
        exit(1)
elif take_sample == "n":
    print("Usando muestra completa.")
else:
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

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

for k, i in enumerate(df[df.milenio_dummy].index, start=1):

    url = df["url_0"][i]
    soup, status_code = get_soup(url)

    if soup != 1:

        # add title
        texto = soup.find_all("title")[0].text

        # add body
        for x in soup.find_all("p"):
            texto += " "
            texto += x.text

        df.loc[i, "texto"] = texto[:EXCEL_CHAR_LIMIT]

    else:
        1

    if k % 50 == 0:
        print(f"{k} de {len(df[df.milenio_dummy].index)} completados")

print("milenio completado")

################################################################################
#   get text elsol

for k, i in enumerate(df[df.elsol_dummy].index, start=1):

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

        df.loc[i, "texto"] = texto[:EXCEL_CHAR_LIMIT]

    except:
        1

    df.loc[i, "status_code"] = status_code

    if k % 50 == 0:
        print(f"{k} de {len(df[df.elsol_dummy].index)} completados")

print("elsol completado")

################################################################################
#   get text for the other sites (unstructured)

for k, i in enumerate(df[~df.elsol_dummy & ~df.milenio_dummy].index, start=1):

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
            df.loc[i, "texto"] = texto[:EXCEL_CHAR_LIMIT]

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
#   further process to get features from the text

df["tags"] = df["tags"].str.lower()

df["texto_limpio"] = get_clean_text(df["texto"])

df["texto_lista"] = df.texto_limpio.str.split(" ")

df.loc[df.texto_limpio.isnull(), "texto_limpio"] = ""

df["URL noticia 0"] = df["URL noticia"].copy()
df.loc[df["URL noticia"].isnull(), "URL noticia 0"] = ""

################################################################################
#   classification of cases by medium of transport of the victim

wants_manual_vars = input("¿Tu query es de accidentes viales y quieres las variables manuales? y/n: ")
if wants_manual_vars == "y":

    df["edad"] = np.nan
    for i in df.index:
        df.loc[i, "edad"] = get_edad(df.texto_lista, i)

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

elif wants_manual_vars != "n":

    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

################################################################################
#   export output to file

df.milenio_dummy *= 1
df.elsol_dummy *= 1

df = df.drop(columns=["aux", "url_0", "texto_limpio", "URL noticia 0", "texto_lista"])

print(df.head()['texto'])
custom_output_name = input("¿Deseas poner un nombre específico al archivo de salida? y/n: ")
if custom_output_name == "y":
    OUTPUT_FILE_PATH = input("Introduce nombre de archivo de salida: ")
elif custom_output_name != "n":
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

try:
    df.to_csv(OUTPUT_FILE_PATH, index=False)
except:
    df.to_csv(OUTPUT_FILE_PATH, index=False, encoding="latin1", errors="ignore")

print("Hecho! en", (time() - start) / 60, "min")
