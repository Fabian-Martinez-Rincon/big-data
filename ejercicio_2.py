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
    .appName("TP1 - Punto 2 (promedio de puntajes)") \
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

rdd = sc.textFile(input_file)

# Cada línea: id_retador id_retado puntaje tiempo
def parse_line(line):
    parts = line.strip().split()
    if len(parts) >= 3:
        id_retador = parts[0]
        puntaje = int(parts[2])       # Columna de puntaje
        return (id_retador, (puntaje, 1))
    return None

# ===========================
# MAPEO Y REDUCCIÓN
# ===========================
rdd_pares = rdd.map(parse_line).filter(lambda x: x is not None)

# Sumamos puntos y combates por jugador
rdd_sum = rdd_pares.reduceByKey(
    lambda a, b: (a[0] + b[0], a[1] + b[1])
)

# Aplicamos la fórmula (puntos + 1) / (combates + 1)
rdd_promedios = rdd_sum.mapValues(lambda x: (x[0] + 1) / (x[1] + 1))

# ===========================
# BUSCAR EL MÁXIMO PROMEDIO
# ===========================
mejor = rdd_promedios.max(key=lambda x: x[1])

print("\nConsulta 2:")
print(f"El jugador con más puntos en promedio: Jugador {mejor[0]} con {mejor[1]:.2f}")

spark.stop()
