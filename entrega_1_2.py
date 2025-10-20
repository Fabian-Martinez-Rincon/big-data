import os, re
from MRE import Job

# ==============================
# CONFIGURACIÓN
# ==============================
class Config:
    BASE = os.path.join(os.getcwd(), "Datasets", "TP1")
    INPUT = os.path.join(BASE, "input")
    OUT1  = os.path.join(BASE, "out_filtrar")
    OUT2  = os.path.join(BASE, "out_pp")
    OUT3  = os.path.join(BASE, "out_ph")

    for path in [INPUT, OUT1, OUT2, OUT3]:
        os.makedirs(path, exist_ok=True)

# ==============================
# UTILIDADES
# ==============================
class JobUtils:
    @staticmethod
    def leer_resultados(path):
        res = {}
        try:
            archivos = [f for f in os.listdir(path) if f.startswith(("part", "output"))]
            if not archivos:
                print(f"[WARN] No hay archivos en {path}")
                return res

            with open(os.path.join(path, archivos[0]), "r", encoding="utf-8") as f:
                for line in f:
                    if "\t" not in line: continue
                    k, v = line.strip().split("\t", 1)
                    try:
                        res[int(k)] = float(v.strip().replace("(", "").replace(")", "").replace(",", ""))
                    except ValueError:
                        pass
        except FileNotFoundError:
            print(f"[WARN] No existe: {path}")
        return res

    @staticmethod
    def guardar_top10(data, path):
        with open(os.path.join(path, "top10.txt"), "w", encoding="utf-8") as f:
            for j, p in data:
                f.write(f"{j}\t{p:.2f}\n")


# ==============================
# CLASE BASE
# ==============================
class JobBase:
    def __init__(self, input_path, output_path, fmap, fred):
        self.input_path = input_path
        self.output_path = output_path
        self.fmap = fmap
        self.fred = fred

    def run(self, params=None):
        job = Job(self.input_path, self.output_path, self.fmap, self.fred)
        if params:
            job.setParams(params)
        job.waitForCompletion()
        return JobUtils.leer_resultados(self.output_path)


# ==============================
# JOB 1: FILTRADO
# ==============================
class FiltradoJob(JobBase):
    @staticmethod
    def fmap(key, value, context):
        try:
            retador, puntos, tiempo = value.strip().split()
            context.write(retador, (float(puntos), float(tiempo)))
        except Exception:
            pass

    @staticmethod
    def fred(key, values, context):
        for v in values:
            context.write(key, v)


# ==============================
# JOB 2: PROMEDIO DE PUNTAJE
# ==============================
class PromedioJob(JobBase):
    @staticmethod
    def fmap(key, value, context):
        puntos, tiempo = value if isinstance(value, tuple) else map(float, value.strip().split())
        context.write(key, ("P", puntos))

    @staticmethod
    def fred(key, values, context):
        puntos = [v for tag, v in values if tag == "P"]
        if puntos:
            context.write(key, sum(puntos) / len(puntos))


# ==============================
# JOB 3: PUNTAJE HEROICO
# ==============================
class PuntajeHeroicoJob(JobBase):
    @staticmethod
    def fmap(retador, value, context):
        parts = re.split(r'[\t\s]+', value.strip())
        if len(parts) != 3:
            return

        retado, puntos, tiempo = map(float, parts)
        retador, retado = int(retador), int(retado)

        pp, ph_prev, alpha = context["pp"], context["ph_prev"], context["alpha"]

        if retador not in pp or retado not in pp or retado not in ph_prev or pp[retado] == 0:
            return

        contrib = ph_prev[retado] * (pp[retador] / pp[retado])
        context.write(retador, contrib)

    @staticmethod
    def fred(jugador, values, context):
        vals = list(values)
        if not vals:
            return
        alpha = context["alpha"]
        nuevo_ph = alpha * sum(vals) + (1 - alpha)
        context.write(jugador, nuevo_ph)


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print(f"[INFO] Iniciando pipeline de 3 Jobs")

    # Job 1
    job1 = FiltradoJob(Config.INPUT, Config.OUT1, FiltradoJob.fmap, FiltradoJob.fred)
    job1.run()

    # Job 2
    job2 = PromedioJob(Config.OUT1, Config.OUT2, PromedioJob.fmap, PromedioJob.fred)
    pp = job2.run()

    # Job 3 iterativo
    alpha, error, max_iter = 0.202, 0.1, 20
    ph = {j: 1.0 for j in pp.keys()}
    ph_job = PuntajeHeroicoJob(Config.INPUT, Config.OUT3, PuntajeHeroicoJob.fmap, PuntajeHeroicoJob.fred)

    for i in range(max_iter):
        print(f"\n[Iteración {i+1}]")
        nuevo_ph = ph_job.run({"pp": pp, "ph_prev": ph, "alpha": alpha})
        if not nuevo_ph: break

        dif = sum(abs(nuevo_ph[j] - ph.get(j, 0)) for j in nuevo_ph) / len(nuevo_ph)
        print(f"Δ = {dif:.4f}")
        ph = nuevo_ph
        if dif < error:
            print(f"[OK] Convergencia en {i+1} iteraciones.")
            break

    top10 = sorted(ph.items(), key=lambda x: x[1], reverse=True)[:10]
    JobUtils.guardar_top10(top10, Config.OUT3)
    print(f"[INFO] Pipeline finalizado con {len(ph)} jugadores procesados.")
