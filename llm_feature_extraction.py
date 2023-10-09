import os
import pandas as pd
import openai
from dotenv import load_dotenv

################################################################################
# load env

load_dotenv()

openai.organization = os.getenv("OPENAI_ORG_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()

################################################################################

def output_to_dict(output):

    output = output.split('\n')
    output = [x for x in output if x!='']
    
    if len(output)>0:
    
        dict_keys = []
        dict_values = []
        for x in output:
            
            if len(x.split(': '))==2:
                a, b = x.split(': ')
                dict_keys.append(a)
                dict_values.append(b)
            
        out_dict = dict(zip(dict_keys,dict_values))
        
        return out_dict
    
################################################################################
# def filenames

custom_filename = input("¿Cuentas con un archivo csv particular? y/n: ")
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

vars_prompt = "fecha del evento, edad de la víctima, transporte del victimario, transporte de la víctima y ubicación del accidente"
custom_prompt = input("¿Cuentas con una lista de variables personalizada? y/n: ")
if custom_filename == "y":
    vars_prompt = input("Introduce tu lista personalizada: ")
elif custom_filename != "n":
    print("Comando desconocido. Interrumpiendo programa.")
    exit(1)

#prompt_0 = f"Extraer {vars_prompt}:\n "
prompt_0 = f"Extract {vars_prompt}:\n "

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
    ~df.texto_0.str.contains('weve detected|requested url|requested resource|access the url',case=False) & 
    ~df.texto_0.str.contains('error 404',case=False) & 
    df.texto.notnull()
    ].head(40).index:

    # set up the prompt and model parameters
    prompt = prompt_0
    prompt += df.loc[i, 'texto']
    df.loc[i, 'prompt_length'] = len(prompt)
    prompt = prompt[:4097]

    model = "text-davinci-003"    
    try:
        # make the request to the OpenAI API
        response = openai.Completion.create(
          engine=model,
          prompt=prompt,
          max_tokens=1900,
          n=1,
          stop=None,
          temperature=0,
        )
        output = response.choices[0].text

    except Exception as error:
        print('Caught this error: ' + repr(error))
        output = ''
    
    df.loc[i, 'llm_output'] = output
    
    out_dict = output_to_dict(output)    
    if out_dict!=None:    
        for key, value in out_dict.items():
            if key in df.columns:
                df.loc[i, key] = value
            
    print(i)

################################################################################
# export

df.to_csv(OUTPUT_FILE_PATH, 
          index=False, encoding='latin1', errors='ignore')