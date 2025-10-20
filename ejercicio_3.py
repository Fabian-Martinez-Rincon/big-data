from pyspark.sql import SparkSession
import os

# ===========================
# CONFIGURACIÓN DEL ENTORNO
# ===========================
os.environ["JAVA_HOME"] = r"C:\Program Files\Java\jdk-17"
os.environ["PATH"] = os.environ["JAVA_HOME"] + r"\bin;" + os.environ["PATH"]
os.environ["PYSPARK_PYTHON"] = "python"
os.environ["PYSPARK_DRIVER_PYTHON"] = "python"

# ===========================
# INICIO DE SPARK
# ===========================
spark = SparkSession.builder \
    .appName("TP1 - Punto 3 (oponentes distintos)") \
    .master("local[*]") \
    .getOrCreate()

sc = spark.sparkContext
sc.setLogLevel("ERROR")

# ===========================
# PARÁMETRO H
# ===========================
H = 12

# ===========================
# LECTURA DE DATOS
# ===========================
input_file = r"C:\Users\Fabian\Desktop\big-data\Datasets\TP1\input\jugadores.txt"

if not os.path.exists(input_file):
    print(f"❌ Archivo no encontrado: {input_file}")
    spark.stop()
    exit()

rdd = sc.textFile(input_file)

# Cada línea: id_retador id_retado puntaje tiempo
def parse_line(line):
    parts = line.strip().split()
    if len(parts) >= 2:
        id_retador = parts[0]
        id_retado  = parts[1]
        return (id_retador, id_retado)
    return None

# ===========================
# MAPEO Y REDUCCIÓN
# ===========================
rdd_pairs = rdd.map(parse_line).filter(lambda x: x is not None)

# Agrupamos por retador → lista de oponentes
rdd_grouped = rdd_pairs.groupByKey()

# Contamos oponentes distintos
rdd_counts = rdd_grouped.mapValues(lambda vals: len(set(vals)))

# Filtramos los jugadores con más de H oponentes distintos
jugadores = rdd_counts.filter(lambda x: x[1] >= H).keys().collect()

# ===========================
# RESULTADO FINAL
# ===========================
print("\nConsulta 3:")
print(f"Con H = {H}")
print(f"Jugadores que retaron a más de {H} oponentes distintos: {jugadores}")

spark.stop()
