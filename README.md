<img src="numv_logo.png" width="30%" />

https://niunamuertevial.mx/

Repositorio ideado para apoyar al proyecto ni una muerte vial en la recolección de datos.

## Instrucciones de uso

1. Ubicar insumo (archivo excel con lista de sitios de noticias) dentro del repositorio.
2. Ejecutar los siguientes comandos en la terminal (se requiere conda):
```
conda env create -f environment.yml
conda activate niunamuertevial
python main.py
```
3. Se generará un archivo adicional con los datos añadidos.

Nota: En promedio, el programa tarda 1.5 seg por registro, con una complejidad lineal.

### Uso sin conda

Es posible ejecutar este proyecto en cualquier entorno con python instalando los
requisitos listados en `requirements.txt`. Una opción es la siguiente:

```shell-session
$ python -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
(.venv) $ python main.py
```

## Lógica general del programa

1. Lee el insumo (archivo excel con lista de sitios de noticias).
2. Realiza una consulta web a cada url para obtener su estructura html.
3. Se extrae el texto de la nota de cada html. La estructura html varía por periódico.
4. Procesa el texto para obtener variables de interés (edad de la víctima, medio de transporte de la víctima, etc.).
5. Exporta el resultado a un archivo csv.

## Próximos pasos

- Añadir más sitios de noticias para ampliar alcance.
- Refinar reglas de decisión para determinar medio de transporte de la víctima.
- Aligerar carga de environment.yml quitando paquetes innecesarios.
- Refactorizar script main.py.
