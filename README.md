# Big Data

---

- [Notas Clase 1](#notas-clase-1)
- [Practica 1](/practica_1_map_reduce/practica_1.ipynb)
- [Practica 2](/practica_2_hadoop_mapReduce/practica_2.ipynb)

---

Creamos el entorno
```
python -m venv venv
```

Activamos el entorno

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\venv\Scripts\Activate
```

```
pip install --upgrade pip
pip install jupyterlab
```

```
jupyter lab
```

---

## Notas Clase 2

### Repaso del Paradigma MapReduce

- MapReduce organiza el procesamiento en **jobs** como unidad mínima de trabajo
- Cada job se divide en fases **map** y **reduce**
- Los datos llegan en formato de tuplas clave-valor
- Cada mapper procesa solo una porción de los datos sin conocer el contexto global
- Los reducers reciben claves generadas por los mappers y todos los valores asociados a cada clave
- El iterador de valores en la fase reduce solo puede recorrerse una vez y no se puede indexar

### La Función Combiner para Optimización

- El principal problema de MapReduce es el volumen de datos intermedios transferidos entre nodos
- La función Combiner es una optimización que minimiza la cantidad de datos transferidos
- Se ejecuta en el mismo nodo donde se ejecutó el mapper, trabajando con datos en memoria RAM
- Se invoca cuando el buffer de memoria se llena, antes de escribir a disco
- No hay garantía de cuántas veces se ejecutará (es una optimización opcional)
- La entrada y salida deben tener la misma estructura (K2V2)
- En la mayoría de casos, la función Combiner es idéntica a la función Reduce

### Beneficios del Combiner

- Reduce significativamente el volumen de datos intermedios
- Optimiza el uso de memoria RAM
- Minimiza la transferencia de datos a través de la red del cluster
- Ejemplo: En WordCount, si una palabra aparece 100 veces en un split, el Combiner reduce estos 100 pares a un solo par (palabra, 100)

### Problemas Complejos

- Algunos problemas requieren cálculos que no pueden resolverse en un solo job
- Ejemplo: Calcular el desvío estándar de compras en un hipermercado
    - Requiere conocer el promedio primero
    - Como el iterador de valores solo puede recorrerse una vez, necesitamos dos jobs:
        1. Primer job para calcular el promedio
        2. Segundo job para calcular el desvío estándar usando el promedio

### Próximo Tema

- En el segundo video se abordará cómo resolver problemas que requieren la ejecución de más de un job
- También se tratarán casos donde es útil enviar información extra a los mappers y reducers