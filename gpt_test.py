import os
import pandas as pd
import openai
from dotenv import load_dotenv

################################################################################

load_dotenv()

openai.organization = "org-hCHXZmK4qtKP5ZQeCqtB9MV1"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()

INPUT_FILE_PATH = 'output_data.csv'
OUTPUT_FILE_PATH = 'gpt_output_data.csv'

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

df = pd.read_csv(INPUT_FILE_PATH, 
                 encoding='latin1')

df['texto_0'] = df.texto.copy()
df.loc[df.texto.isnull(), 'texto_0'] = ''

df['gpt_output'] = ''
df['Fecha del evento'] = ''
df['Edad de la víctima'] = ''
df['Transporte del victimario'] = ''
df['Transporte de la víctima'] = ''
df['Ubicación del accidente'] = ''

################################################################################

for i in df[ 
    ~df.texto_0.str.contains('weve detected|requested url|requested resource|access the url',case=False) & 
    ~df.texto_0.str.contains('error 404',case=False) & 
    df.texto.notnull()
    ].head(10).index:
    
    
    # set up the prompt and model parameters
    prompt = "Extraer fecha del evento, edad de la víctima, transporte del victimario, transporte de la víctima y ubicación del accidente:\n "
    prompt += df.loc[i, 'texto']
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
    
    df.loc[i, 'gpt_output'] = output
    
    out_dict = output_to_dict(output)
    
    if out_dict!=None:
    
        for key, value in out_dict.items():
            
            if key in df.columns:
                df.loc[i, key] = value
            
    print(i)

################################################################################

df.to_csv(OUTPUT_FILE_PATH, 
          index=False, encoding='latin1', errors='ignore')