from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, row_number
from pyspark.sql.window import Window
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
    .appName("TP1 - Punto 1 (jugadores.txt)") \
    .master("local[*]") \
    .getOrCreate()

sc = spark.sparkContext
sc.setLogLevel("ERROR")

# ===========================
# LECTURA DE DATOS
# ===========================
input_file = r"C:\Users\Fabian\Desktop\big-data\Datasets\TP1\input\jugadores.txt"

if not os.path.exists(input_file):
    print(f"❌ Archivo no encontrado: {input_file}")
    spark.stop()
    exit()

# Leemos el archivo
rdd = sc.textFile(input_file)

# Cada línea: id_retador id_retado puntaje tiempo
def parse_line(line):
    parts = line.strip().split()
    if len(parts) >= 2:
        id_retador = parts[0]
        id_retado  = parts[1]
        return [("RETADOR", id_retador), ("RETADO", id_retado)]
    return []

# Convertimos a pares (rol, jugador)
rdd_roles = rdd.flatMap(parse_line)

# ===========================
# CONTEO Y SELECCIÓN
# ===========================
conteo = (
    rdd_roles
    .map(lambda x: ((x[0], x[1]), 1))
    .reduceByKey(lambda a, b: a + b)
)

# Reestructuramos como DataFrame para usar ventana
df = conteo.map(lambda x: (x[0][0], x[0][1], x[1])).toDF(["rol", "jugador", "apariciones"])

# Ventana para obtener el jugador con más apariciones por rol
w = Window.partitionBy("rol").orderBy(desc("apariciones"))
resultado = df.withColumn("rank", row_number().over(w)).filter(col("rank") == 1)

# ===========================
# RESULTADO FINAL
# ===========================
fila_retador = resultado.filter(col("rol") == "RETADOR").collect()[0]
fila_retado  = resultado.filter(col("rol") == "RETADO").collect()[0]

print("\nConsulta 1:")
print(f"El jugador más 'retador': Jugador {fila_retador}")
print(f"El jugador más 'retado': Jugador {fila_retado}")

spark.stop()
