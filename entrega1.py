import sys, os
sys.path.append("..")
from MRE import Job

# ==============================
# RUTAS DE ENTRADA / SALIDA
# ==============================
BASE_DIR = os.path.join(os.getcwd(), "Datasets", "TP1")

input_path  = os.path.join(BASE_DIR, "input")
job1_out    = os.path.join(BASE_DIR, "out_filtrar")
job2_out    = os.path.join(BASE_DIR, "out_pp")
job3_out    = os.path.join(BASE_DIR, "out_ph")

for path in [input_path, job1_out, job2_out, job3_out]:
    os.makedirs(path, exist_ok=True)

def fmap_filtrar(key, value, context):
    try:
        parts = value.strip().split()
        if len(parts) != 3:
            print(f"[WARN][JOB1] Línea inválida ignorada: {value.strip()}")
            return
        retador, puntos, tiempo = parts
        puntos, tiempo = float(puntos), float(tiempo)
        context.write(retador, (puntos, tiempo))
    except Exception as e:
        print(f"[ERROR][JOB1] {value.strip()} ({e})")

def fred_filtrar(key, values, context):
    for v in values:
        context.write(key, v)

def fmap_pp(key, value, context):
    try:
        if isinstance(value, tuple):
            puntos, tiempo = value
        else:
            puntos, tiempo = map(float, value.strip().split())
        context.write(key, ("P", puntos))
        context.write(key, ("T", tiempo))
    except Exception as e:
        print(f"[ERROR][JOB2] {key} -> {value} ({e})")

def fred_pp(key, values, context):
    total_p, n = 0.0, 0
    for tag, val in values:
        if tag == "P":
            total_p += val
            n += 1
    if n > 0:
        promedio = total_p / n
        context.write(key, promedio)

import re

def fmap_ph(retador, value, context):
    parts = re.split(r'[\t\s]+', value.strip())
    if len(parts) != 3:
        print(f"[WARN][JOB3] Línea inválida: {value.strip()}")
        return

    retado, puntos, tiempo = map(float, parts)
    retador = int(retador)
    retado = int(retado)

    pp = context["pp"]
    ph_prev = context["ph_prev"]
    alpha = context["alpha"]

    if retador not in pp or retado not in pp or retado not in ph_prev:
        return
    if pp[retado] == 0:
        return

    contrib = ph_prev[retado] * (pp[retador] / pp[retado])
    context.write(retador, contrib)

def fred_ph(jugador, values, context):
    vals = list(values)
    if not vals:
        print(f"[REDUCE][JOB3] Jugador {jugador} sin contribuciones.")
        return

    total = sum(vals)
    alpha = context["alpha"]
    nuevo_ph = alpha * total + (1 - alpha)

    context.write(jugador, nuevo_ph)


def leer_resultados(path):
    res = {}
    try:
        archivos = [f for f in os.listdir(path) if f.startswith("part") or f.startswith("output")]
        if not archivos:
            print(f"[WARN] No se encontró ningún archivo en {path}")
            return res

        file_path = os.path.join(path, archivos[0])
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "\t" not in line:
                    continue
                k, v = line.split("\t", 1)
                try:
                    res[int(k)] = float(v.strip().replace("(", "").replace(")", "").replace(",", ""))
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"[WARN] Carpeta no encontrada: {path}")
    print(f"[DEBUG] Leídos {len(res)} resultados desde {path}")
    return res

def guardar_top10(top10, path):
    out_path = os.path.join(path, "top10.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for j, p in top10:
            f.write(f"{j}\t{p:.2f}\n")

if __name__ == "__main__":
    print(f"\n[DEBUG] Archivos en {input_path}: {os.listdir(input_path)}")

    print("\n========== INICIANDO JOB 1: FILTRADO ==========")
    job1 = Job(input_path, job1_out, fmap_filtrar, fred_filtrar)
    job1.waitForCompletion()
    print("[OK] Job 1 completado")

    print("\n========== INICIANDO JOB 2: PROMEDIO DE PUNTAJES ==========")
    job2 = Job(job1_out, job2_out, fmap_pp, fred_pp)
    job2.waitForCompletion()
    pp = leer_resultados(job2_out)
    max_pp = max(pp.values())

    print(f"[OK] Job 2 completado | Jugadores con PP calculado: {len(pp)}")

    print("\n========== INICIANDO JOB 3: PUNTAJE HEROICO ==========")
    jugadores = set(pp.keys())
    with open(os.path.join(input_path, "jugadores.txt"), "r", encoding="utf-8") as f:
        for linea in f:
            partes = linea.strip().split()
            if len(partes) == 4:
                jugadores.add(int(partes[1]))
    ph = {j: 1.0 for j in jugadores}

    alpha, error, max_iter = 0.202, 0.1, 20

    for i in range(max_iter):
        print(f"\n---- Iteración {i+1} ----")
        combates_path = os.path.join(input_path)
        print("Archivos disponibles:", os.listdir(input_path))
        assert os.path.exists(combates_path), f"Archivo no encontrado: {combates_path}"
        job3 = Job(combates_path, job3_out, fmap_ph, fred_ph)

        job3.setParams({"pp": pp, "ph_prev": ph, "alpha": alpha})
        job3.waitForCompletion()

        nuevo_ph = leer_resultados(job3_out)
        if not nuevo_ph:
            print("[WARN] No se obtuvieron nuevos PH (ver mapa de JOB3)")
            break

        dif = sum(abs(nuevo_ph[j] - ph.get(j, 0)) for j in nuevo_ph) / len(nuevo_ph)
        print(f"[INFO] Iter {i+1} | Diferencia promedio Δ={dif:.4f}")

        ph = nuevo_ph
        if dif < error:
            print(f"[INFO] Convergencia alcanzada en {i+1} iteraciones.")
            break

    print("\n========== TOP 10 FINAL ==========")
    top10 = sorted(ph.items(), key=lambda x: x[1], reverse=True)[:10]
    for j, p in top10:
        print(f"(Jugador = {j}, PH = {p:.2f})")
    guardar_top10(top10, job3_out)
    print(f"[OK] Resultados guardados en: {job3_out}")
