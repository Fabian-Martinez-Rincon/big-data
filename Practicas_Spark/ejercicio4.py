from collections import defaultdict

# Parámetros
ALFA = 0.1
PH_INICIAL = 1.0
ERROR = 0.1
MAX_ITER = 20
PATH = r"jugadores.txt"


def leer_datos(path):
    combates = []
    with open(path, "r", encoding="utf-8") as f:
        for linea in f:
            parts = linea.strip().split()
            if len(parts) >= 4:
                try:
                    retador = int(parts[0])
                    retado = int(parts[1])
                    puntos = float(parts[2])
                    tiempo = float(parts[3])
                    combates.append((retador, retado, puntos, tiempo))
                except ValueError:
                    continue
    print(f"[INFO] Combates cargados correctamente: {len(combates)}")
    return combates


def filtrar_menor_tiempo(combates):
    mejores = {}
    for retador, retado, puntos, tiempo in combates:
        clave = (retador, retado)
        if clave not in mejores or tiempo < mejores[clave][1]:
            mejores[clave] = (puntos, tiempo)
    return [(r, o, p, t) for (r, o), (p, t) in mejores.items()]


def calcular_pp(combates):
    suma = defaultdict(float)
    cuenta = defaultdict(int)
    for retador, retado, puntos, _ in combates:
        suma[retador] += puntos
        cuenta[retador] += 1
        if retado not in cuenta:
            cuenta[retado] = 0
            suma[retado] = 0.0
    for j in cuenta:
        if cuenta[j] == 0:
            cuenta[j] = 1
            suma[j] = 1.0
    pp = {j: suma[j] / cuenta[j] for j in cuenta}
    return pp


def obtener_relaciones(combates):
    relaciones = defaultdict(list)
    for retador, retado, _, _ in combates:
        relaciones[retador].append(retado)
    return relaciones


def calcular_ph(combates):
    combates = filtrar_menor_tiempo(combates)
    pp = calcular_pp(combates)
    relaciones = obtener_relaciones(combates)
    jugadores = set(pp.keys()) | set(relaciones.keys())
    ph = {j: PH_INICIAL for j in jugadores}

    for it in range(MAX_ITER):
        nuevo_ph = {}
        max_dif = 0.0

        for i in jugadores:
            if i not in relaciones or len(relaciones[i]) == 0:
                nuevo_ph[i] = ph[i]
                continue

            suma = 0.0
            for j in relaciones[i]:
                if pp[j] > 0:
                    suma += ph[j] * (pp[i] / pp[j])

            nuevo_ph[i] = ALFA * suma + (1 - ALFA)
            max_dif = max(max_dif, abs(nuevo_ph[i] - ph[i]))

        ph = nuevo_ph
        if max_dif < ERROR:
            print(f"[INFO] Convergencia alcanzada en iteración {it + 1}.")
            break

    return ph


def top_10(ph):
    return sorted(ph.items(), key=lambda x: x[1], reverse=True)[:10]


if __name__ == "__main__":
    combates = leer_datos(PATH)
    ph = calcular_ph(combates)
    top = top_10(ph)

    print("\nConsulta 4:")
    print(f"Con alfa = {ALFA}; puntaje heroico inicial = {PH_INICIAL}; cota de error = {ERROR} ({MAX_ITER} iteraciones)")
    print("El top 10 de los jugadores con mejor puntaje heroico:")
    for j, p in top:
        print(f"(Jugador = {j}, Puntaje heroico = {p:.1f})")
