import os
import warnings
from pyspark.sql import SparkSession


def configure_java(jdk_path: str = r"C:\Program Files\Java\jdk-17") -> None:
    """Configura las variables de entorno necesarias para PySpark."""
    if not os.path.exists(jdk_path):
        raise FileNotFoundError(f"No se encontró el JDK en la ruta: {jdk_path}")
    os.environ["JAVA_HOME"] = jdk_path
    os.environ["PATH"] = os.path.join(jdk_path, "bin") + ";" + os.environ["PATH"]


def create_spark_session(app_name: str = "TestSparkLocal", master: str = "local[*]") -> SparkSession:
    """Crea una sesión Spark configurada en modo local."""
    warnings.filterwarnings("ignore")  # Oculta advertencias irrelevantes

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.ui.showConsoleProgress", "false")  # Limpia la consola
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")  # Muestra solo errores importantes
    return spark


if __name__ == "__main__":
    configure_java()  # Detecta automáticamente el JDK configurado
    spark = create_spark_session()

    print(f"✅ Spark iniciado correctamente — versión: {spark.version}")
    spark.range(5).show()

    spark.stop()
