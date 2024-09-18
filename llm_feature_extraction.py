import os
import pandas as pd
import openai
from dotenv import load_dotenv
import json

################################################################################
# load env

load_dotenv()

openai.organization = os.getenv("OPENAI_ORG_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

################################################################################
# def funcitions
    
def output_to_dict(output):
    output = output.split("```")[1]
    output = output.replace('\n','').replace('json','')
    output = json.loads(
        output    
    )
    return output

################################################################################
# def filenames

custom_filename = input("¿Cuentas con un archivo csv con un nombre distinto al default del programa anterior? y/n: ")
if custom_filename == "y":
    INPUT_FILE_PATH = input("Introduce el nombre del archivo csv: ")
elif custom_filename == "n":
    INPUT_FILE_PATH = 'output_data.csv'
else:
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

OUTPUT_FILE_PATH = 'llm_' + INPUT_FILE_PATH

################################################################################
# prepare prompt

vars_prompt = "fecha del evento, nombre de la víctima, género de la víctima, edad de la víctima, nombre del victimario, edad del victimario, género del victimario, transporte del victimario, medio de transporte de la víctima, si la víctima salió volando,  si la víctima tomó alcohol, si el victimario tomó alcohol, ubicación del accidente, municipio del accidente, localidad del accidente, en cuántos días murió la víctima, cómo murió la víctima y si el victimario fue detenido"
# vars_prompt = "fecha del evento, edad de la víctima, transporte del victimario, transporte de la víctima y ubicación del accidente"
custom_prompt = input("¿Cuentas con una lista de variables personalizada? y/n: ")
if custom_prompt == "y":
    vars_prompt = input("Introduce tu lista personalizada: ")
elif custom_prompt != "n":
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

#prompt_0 = f"Extraer {vars_prompt}:\n "
prompt_0 = f"Extrae en formato json las variables {vars_prompt}:\n "

################################################################################
# read dataset

df = pd.read_csv(INPUT_FILE_PATH,
                 encoding='latin1')

df['texto_0'] = df.texto.copy()
df.loc[df.texto.isnull(), 'texto_0'] = ''

list_vars_prompt = vars_prompt.split(', ')
list_vars_prompt = list_vars_prompt[:-1] + list_vars_prompt[-1].split(" y ")

df['prompt_length'] = -1
df['llm_output'] = ''
for var in list_vars_prompt:
    aux = var.capitalize()
    df[aux] = ''

################################################################################
# perform requests

for i in df[ 
    (~df.texto_0.str.contains('weve detected|requested url|requested resource|access the url',case=False)) & 
    (~df.texto_0.str.contains('error 404',case=False)) & 
    (df['URL noticia'].str.slice(-4)!='.pdf') & 
    (df.texto.notnull())
    ].index:

    # set up the prompt and model parameters
    MODEL = "gpt-4o-mini"
    LLM_MODEL_TOKEN_LIMIT = 128000
    # rule assuming conservatively that tokens (words) have 3 characters on average
    LLM_MODEL_CHAR_LIMIT = 3*LLM_MODEL_TOKEN_LIMIT

    prompt = prompt_0
    prompt += df.loc[i, 'texto']
    df.loc[i, 'prompt_length'] = len(prompt)
    prompt = prompt[:LLM_MODEL_CHAR_LIMIT]

    try:
        # make the request to the OpenAI API
        response = openai.chat.completions.create(
          model=MODEL,
          messages=[{'role':'user','content':prompt}]
        )
        output = response.choices[0].message.content
        print(df['URL noticia'][i])

    except Exception as error:
        print('Caught this error: ' + repr(error))
        output = ''
    
    df.loc[i, 'llm_output'] = output
    
    try:
        out_dict = output_to_dict(output)
        out_list = list(out_dict.values())    
        for j in range(len(out_list)):
            df.iloc[i, -(1+j)] = out_list[-(1+j)]

    except Exception as error:
        print('Caught this error: ' + repr(error))
            
    print(i)
    print(output)

################################################################################
# export

df.to_csv(OUTPUT_FILE_PATH, 
          index=False, encoding='latin1', errors='ignore')