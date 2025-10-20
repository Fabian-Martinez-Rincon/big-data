from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split, trim, lit, sum as _sum, count
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
    .appName("TP1 - Spark pipeline (Puntaje Heroico)") \
    .master("local[*]") \
    .getOrCreate()

sc = spark.sparkContext
sc.setLogLevel("ERROR")

# ===========================
# RUTA DE ARCHIVO
# ===========================
input_file = r"C:\Users\Fabian\Desktop\big-data\Datasets\TP1\input\jugadores.txt"

if not os.path.exists(input_file):
    print(f"❌ Archivo no encontrado: {input_file}")
    spark.stop()
    exit()

# ===========================
# JOB 1 - FILTRADO
# ===========================
print("\n========== JOB 1: FILTRADO ==========")

# Lectura robusta (maneja múltiples espacios o tabs)
df_raw = spark.read.text(input_file)

df = (
    df_raw.withColumn("cols", split(trim(col("value")), r"\s+"))
          .select(
              col("cols").getItem(0).alias("id_retador"),
              col("cols").getItem(1).alias("id_retado"),
              col("cols").getItem(2).alias("puntos"),
              col("cols").getItem(3).alias("tiempo")
          )
          .select(
              col("id_retador").cast("int"),
              col("id_retado").cast("int"),
              col("puntos").cast("double"),
              col("tiempo").cast("double")
          )
)

df.show(5, truncate=False)
print(f"[OK] Registros válidos: {df.count()}")

# ===========================
# JOB 2 - PROMEDIO DE PUNTAJES
# ===========================
print("\n========== JOB 2: PROMEDIO DE PUNTAJES ==========")

df_sum = df.groupBy("id_retador").agg(
    ((_sum("puntos") + lit(1)) / (count("*") + lit(1))).alias("pp")
)

pp_dict = {int(r["id_retador"]): float(r["pp"]) for r in df_sum.collect()}
print(f"[OK] Promedios calculados: {len(pp_dict)} jugadores")

# ===========================
# JOB 3 - PUNTAJE HEROICO (ITERATIVO)
# ===========================
print("\n========== JOB 3: PUNTAJE HEROICO ==========")

# Dataset base
df_base = df.selectExpr(
    "cast(id_retador as int) as retador",
    "cast(id_retado as int) as retado",
    "cast(puntos as double) as puntos",
    "cast(tiempo as double) as tiempo"
)

# Inicialización PH
jugadores = set(pp_dict.keys()) | set([int(r["retado"]) for r in df_base.select("retado").distinct().collect()])
ph = {j: 1.0 for j in jugadores}

# Parámetros
alpha, error, max_iter = 0.1, 0.1, 20

for i in range(max_iter):
    print(f"\n---- Iteración {i+1} ----")

    # DataFrames de apoyo
    df_pp = spark.createDataFrame(pp_dict.items(), ["jugador", "pp"])
    df_ph = spark.createDataFrame(ph.items(), ["jugador", "ph_prev"])

    # JOINS flexibles
    df_join = (
        df_base
        .join(df_pp.withColumnRenamed("jugador", "retador"), on="retador", how="left")
        .withColumnRenamed("pp", "pp_retador")
        .join(df_pp.withColumnRenamed("jugador", "retado"), on="retado", how="left")
        .withColumnRenamed("pp", "pp_retado")
        .join(df_ph.withColumnRenamed("jugador", "retado"), on="retado", how="left")
        .withColumnRenamed("ph_prev", "ph_prev_retado")
        .fillna({"pp_retador": 1.0, "pp_retado": 1.0, "ph_prev_retado": 1.0})
    )

    print(f"[DEBUG] Registros join: {df_join.count()}")

    # Contribuciones
    df_contrib = df_join.withColumn(
        "contrib", col("ph_prev_retado") * (col("pp_retador") / col("pp_retado"))
    ).select("retador", "contrib")

    df_sum_contrib = df_contrib.groupBy("retador").agg(_sum("contrib").alias("total"))
    print(f"[DEBUG] Jugadores con contribución: {df_sum_contrib.count()}")

    # Nuevo PH
    df_new_ph = df_sum_contrib.withColumn("ph", alpha * col("total") + (1 - alpha))
    nuevo_ph = {int(r["retador"]): float(r["ph"]) for r in df_new_ph.collect()}

    if not nuevo_ph:
        print("[WARN] Ningún PH calculado en esta iteración.")
        break

    # Convergencia
    dif = sum(abs(nuevo_ph.get(j, 0) - ph.get(j, 0)) for j in nuevo_ph) / len(nuevo_ph)
    print(f"[INFO] Δ promedio = {dif:.4f}")

    ph = nuevo_ph
    if dif < error:
        print(f"[INFO] ✅ Convergencia alcanzada en iteración {i+1}")
        break

# ===========================
# TOP 10 FINAL
# ===========================
print("\n========== TOP 10 FINAL ==========")
top10 = sorted(ph.items(), key=lambda x: x[1], reverse=True)[:10]
for j, p in top10:
    print(f"(Jugador = {j}, Puntaje heroico = {p:.2f})")

spark.stop()
