# Big Data

---

- [📕 Practica 1](practica_1.ipynb)
- [📒 Notas Clase 2](#notas-clase-2)
- [📕 Practica 2](practica_2.ipynb)
- [📒 Notas Clase 3](#notas-clase-3)
- [📕 Practica 3](practica_3.ipynb)
- [📒 Notas Clase 4](#notas-clase-4)
- [📕 Practica 4](practica_4.ipynb)

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

---

## Notas Clase 3

### Conceptos Fundamentales

- Los problemas más complejos requieren ejecutar más de un job MapReduce
- Los jobs se ejecutan secuencialmente (un job completo termina antes de iniciar el siguiente)
- DAG (Grafo Acíclico Dirigido) permite visualizar el flujo de procesamiento
- La salida de un job puede servir como entrada para otro job
- Es posible parametrizar funciones Map y Reduce para enviarles información adicional

### Problema del Desvío Estándar

- Requiere calcular primero el promedio (Job 1) y luego usarlo para calcular el desvío (Job 2)
- El dataset completo se utiliza dos veces en jobs diferentes
- El promedio calculado en el primer job debe pasarse como parámetro al segundo job

### Análisis de Logs Web

- Dataset: ID de usuario, ID de página, tiempo de permanencia
- Objetivo: encontrar para cada usuario la página donde pasó más tiempo
- Solución en dos jobs:
    - Job 1: Usa (idUsuario, idPágina) como clave intermedia para acumular tiempos
    - Job 2: Usa idUsuario como clave para encontrar la página con mayor tiempo acumulado

### Algoritmos Iterativos

- Necesitan recorrer el dataset completo varias veces
- Ejemplos: clustering, TF-IDF, PageRank, entrenamiento de redes neuronales
- Método de Jacobi como ejemplo:
    - Resuelve sistemas de ecuaciones lineales iterativamente
    - Cada iteración usa valores de la anterior
    - Termina cuando la diferencia entre iteraciones es menor que un umbral

### Parametrización de Funciones

- Permite pasar información adicional a Map y Reduce
- Se configura desde el driver usando setParams()
- Útil para:
    - Pasar resultados entre jobs (como el promedio al job de desvío estándar)
    - Pasar valores de iteraciones anteriores (como en Jacobi)
    - Compartir configuraciones o datos calculados previamente

### Implementación de Algoritmos Iterativos

- Requiere un bucle (while) en el driver que controle las iteraciones
- Cada iteración ejecuta un job completo
- Los resultados de cada job se usan para:

---

## Notas Clase 4

### Concepto General

El paradigma MapReduce permite implementar operaciones similares a SQL (filtros, resúmenes, transformaciones y JOIN) en entornos de Big Data. En esta clase se utiliza el ejemplo de una base de datos bancaria con tres tablas (Cliente, Caja de Ahorro y Préstamo) almacenadas como archivos en directorios diferentes del HDFS.

### Operaciones Básicas

- **GROUP BY (Agrupación)**: Similar a WordCount, donde la clave del Map es el campo de agrupación y el Reduce implementa la función de agregación.
- **Filtros (WHERE)**: Se implementan en la fase Map para minimizar datos transferidos entre mappers y reducers.
- **Proyecciones (SELECT)**: El Map emite solo los campos necesarios, funcionando como un filtro por columnas.
- **DISTINCT**: Se implementa haciendo que el Reduce escriba solo una tupla para cada clave, ignorando duplicados.

### Operación JOIN

- **Desafío principal**: Las tablas están en directorios diferentes del HDFS.
- **Implementación**:
    - Opción 1: Una única función Map que procesa datos de ambas tablas
    - Opción 2: Dos funciones Map diferentes, una para cada tabla
- **JOIN 1:1 (Caja de Ahorro-Préstamo)**:
    - Map emite el ID de caja como clave para ambas tablas
    - Reduce recibe registros de ambas tablas con la misma clave
    - Se necesita identificar a qué tabla pertenece cada registro (usar etiquetas)
- **JOIN 1:N (Cliente-Caja de Ahorro)**:
    - Más complejo porque un cliente puede tener múltiples cajas de ahorro
    - Es necesario procesar primero los datos del cliente en el Reduce

### Control de Orden en MapReduce

- **Fases Shuffle y Sort**: Etapas intermedias entre Map y Reduce
    - **Shuffle**: Agrupa registros con la misma clave para el mismo Reducer
    - **Sort**: Ordena las claves antes de enviarlas al Reducer
- **Comparadores personalizados**:
    - Comparador Shuffle: Define qué claves son "iguales" para agrupar
    - Comparador Sort: Define el orden en que las claves llegan al Reducer
    - Permiten controlar el orden de procesamiento en joins complejos

### Optimización de Consultas Complejas

- Estrategia de optimización:
    1. Descomponer la consulta en operaciones simples (filtros, joins, agrupaciones)
    2. Crear un grafo dirigido acíclico (DAG) de operaciones
    3. Optimizar combinando múltiples operaciones en menos jobs
    4. Minimizar lecturas/escrituras de datos entre jobs

### Conclusión

La implementación de operaciones complejas en MapReduce requiere pensar en términos de Map y Reduce, personalizar el comportamiento de Shuffle y Sort, y optimizar el flujo de datos para minimizar operaciones de E/S. La próxima clase abordará el framework Spark.

### Reflexión Final

- [ ]  Considerar si es posible implementar toda la consulta compleja presentada al final en un único job MapReduce