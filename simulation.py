import pandas
import random
from utils import generar_exponencial, generar_uniforme

def run_simulation(cfg):
    eventos = cfg['events']
    simulacion = cfg['simulation']

    global MEDIA_LLEGADA, A, B, PROBA_CORRECCION, TIEMPO_CORRECCION
    MEDIA_LLEGADA = eventos['media_llegada']
    A = eventos['minimo_tiempo_servicio']
    B = eventos['maximo_tiempo_servicio']
    PROBA_CORRECCION = eventos['probabilidad_correccion']
    TIEMPO_CORRECCION = eventos['duracion_correccion']
    FIN_TRABAJOS_COMPLETOS = simulacion['fin_trabajos_completos']
    FIN_LINEAS = simulacion['fin_lineas']
    FIN_RELOJ = simulacion['fin_reloj']
    SEMILLA = simulacion['semilla']

    if SEMILLA is not None:
        random.seed(SEMILLA)

    vector = inicializar_vector()
    tabla = [vector]


    eventos = {
    "Llegada1": vector["llegada1"],
    "Llegada2": vector["llegada2"],
    "Llegada3": vector["llegada3"],
    }
    nombre_evento, tiempo_evento = min(eventos.items(), key=lambda x: x[1])
    reloj = tiempo_evento
    
    while True:
        # print(vector)
        # print(vector["trabajos"])
        if FIN_LINEAS is not None and len(tabla) >= FIN_LINEAS:
            break
        if FIN_TRABAJOS_COMPLETOS is not None and vector["cont_trabajos"] >= FIN_TRABAJOS_COMPLETOS:
            break
        if FIN_RELOJ is not None and reloj >= FIN_RELOJ:
            break
        if FIN_TRABAJOS_COMPLETOS is None and FIN_LINEAS is None and FIN_RELOJ is None:
            if vector["cont_trabajos"] >= 5:
                break
        
        anterior = vector.copy()

        if nombre_evento == "Llegada1":
            vector = manejar_llegada1(reloj, anterior)
        elif nombre_evento == "Llegada2":
            vector = manejar_llegada(reloj, anterior, 2)
        elif nombre_evento == "Llegada3":
            vector = manejar_llegada(reloj, anterior, 3)
        elif nombre_evento == "Chequeo Correccion":
            vector = manejar_chequeo_correccion(reloj, anterior, anterior["id_atendido"])
        elif nombre_evento == "Fin Correccion Activo":
            vector = manejar_fin_correccion(reloj, anterior, anterior["id_atendido"])
        elif nombre_evento == "Fin Correccion Suspendido":
            vector = manejar_fin_correcion_suspendido(reloj, anterior, id_corr)
        elif nombre_evento == "Fin servicio":
            vector = manejar_fin_servicio(reloj, anterior, anterior["id_atendido"])

        t_corr, id_corr = proxima_correccion(vector["trabajos"])
        eventos = {
        "Llegada1": vector["llegada1"],
        "Llegada2": vector["llegada2"],
        "Llegada3": vector["llegada3"],
        "Chequeo Correccion": vector["fin_fase"] if vector["fase"] == "primera mitad" else float('inf'),
        "Fin Correccion Activo": vector["fin_fase"] if vector["fase"] == "correccion" else float('inf'),
        "Fin servicio": vector["fin_fase"] if vector["fase"] == "segunda mitad" else float('inf'),
        "Fin Correccion Suspendido": t_corr,
        }
        nombre_evento, tiempo_evento = min(eventos.items(), key=lambda x: x[1])
        reloj = tiempo_evento

        tabla.append(vector)

    tiempo_espera_promedio = vector["ac_espera"] / vector["cont_atendidos"]
    longitud_cola_promedio = vector["suma_area_cola"] / reloj
    promedio_tiempo_sistema = vector["ac_tiempo_sistema"] / vector["cont_trabajos"]

    metricas = (tiempo_espera_promedio, longitud_cola_promedio, promedio_tiempo_sistema)

    return pandas.DataFrame(tabla), metricas

def proxima_correccion(trabajos):
    candidatos = [(t["fin_correccion"], t["id"]) for t in trabajos if t["fin_correccion"] is not None]
    if not candidatos:
        return float("inf"), None
    fin, tid = min(candidatos, key=lambda x: x[0])
    return fin, tid

def inicializar_vector():
    evento = "Inicializacion"
    rnd1 = random.random()
    tiempo_llegada1 = generar_exponencial(MEDIA_LLEGADA, rnd1)
    rnd2 = random.random()
    tiempo_llegada2 = generar_exponencial(MEDIA_LLEGADA, rnd2)
    rnd3 = random.random()
    tiempo_llegada3 = generar_exponencial(MEDIA_LLEGADA, rnd3)

    return {
        "evento": evento,
        "reloj": 0,
        "rnd_llegada1": rnd1,
        "tiempo_llegada1": tiempo_llegada1,
        "llegada1": tiempo_llegada1,
        "rnd_llegada2": rnd2,
        "tiempo_llegada2": tiempo_llegada2,
        "llegada2": tiempo_llegada2,
        "rnd_llegada3": rnd3,
        "tiempo_llegada3": tiempo_llegada3,
        "llegada3": tiempo_llegada3,
        "id_atendido": None,
        "rnd_trabajo": None,
        "duracion_trabajo": None,
        "rnd_correccion": None,
        "correccion": None,
        "fase": None,
        "fin_fase": None,
        "id_suspendido": None,
        "restante": None,
        "restante_fase": None,
        "estado_mecanografa": "libre",
        "cola": 0,
        "cola_prioridad": 0,
        "ac_espera": 0.0,
        "cont_atendidos": 0.0,
        "ac_tiempo_sistema": 0.0,
        "cont_trabajos": 0,
        "ultimo_cambio_cola": 0.0,
        "suma_area_cola": 0.0,
        "trabajos": [],
    }


def manejar_llegada1(reloj, anterior):
    trabajos = anterior["trabajos"]
    nuevo_id = len(trabajos) + 1

    rnd = random.random()
    tiempo_llegada = generar_exponencial(MEDIA_LLEGADA, rnd)
    llegada = reloj + tiempo_llegada

    id_atendido = anterior["id_atendido"]
    rnd_trabajo = None
    duracion_trabajo = None
    fase = anterior["fase"]
    fin_fase = anterior["fin_fase"]

    id_suspendido = anterior["id_suspendido"]
    restante = anterior["restante"]
    restante_fase = anterior["restante_fase"]

    cola_prioridad = anterior["cola_prioridad"]

    cont_atendidos = anterior["cont_atendidos"]
    ultimo_cambio = anterior["ultimo_cambio_cola"]
    suma_area = anterior["suma_area_cola"]
    

    if anterior["estado_mecanografa"] == "libre":
        id_atendido = nuevo_id
        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)
        fin_fase = reloj + duracion_trabajo / 2
        fase = "primera mitad"
        estado_mecanografa = "ocupada 1"
        estado_trabajo = "siendo atendido"
        cont_atendidos += 1
    
    elif anterior["estado_mecanografa"] == "ocupada 1":
        cola_prioridad = anterior["cola_prioridad"] + 1
        estado_mecanografa = "ocupada 1"
        estado_trabajo = "esperando"

    elif anterior["estado_mecanografa"] == "ocupada":
        id_atendido = nuevo_id
        id_suspendido = anterior["id_atendido"]
        restante_fase = anterior["fase"]
        restante = anterior["fin_fase"] - reloj

        trabajos[anterior["id_atendido"] - 1]["estado"] = "suspendido"


        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)
        fin_fase = reloj + duracion_trabajo / 2
        fase = "primera mitad"
        estado_mecanografa = "ocupada 1"
        estado_trabajo = "siendo atendido"
        cont_atendidos += 1

    elif anterior["estado_mecanografa"] == "esperando correccion":
        id_atendido = nuevo_id
        id_suspendido = anterior["id_atendido"]
        restante_fase = "correccion"
        restante = None

        trabajos[anterior["id_atendido"] - 1]["estado"] = "siendo corregido"
        trabajos[anterior["id_atendido"] - 1]["fin_correccion"] = anterior["fin_fase"]

        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)
        fin_fase = reloj + duracion_trabajo / 2
        fase = "primera mitad"
        estado_mecanografa = "ocupada 1"
        estado_trabajo = "siendo atendido"
        cont_atendidos += 1

    elif anterior["estado_mecanografa"] == "esperando correccion 1":
        cola_prioridad = anterior["cola_prioridad"] + 1
        estado_mecanografa = "esperando correccion 1"
        estado_trabajo = "esperando"

    if anterior["cola"] + anterior["cola_prioridad"] != anterior["cola"] + cola_prioridad:
        suma_area = anterior["suma_area_cola"] + (reloj - anterior["ultimo_cambio_cola"]) * (anterior["cola"] + anterior["cola_prioridad"])
        ultimo_cambio = reloj

    nuevo_trabajo = {
        "id": nuevo_id,
        "estado": estado_trabajo,
        "llegada": reloj,
        "prioridad": "especial",
        "duracion_trabajo": duracion_trabajo,
        "fin_correccion": None,
    }

    trabajos.append(nuevo_trabajo)

    vector = {
        "evento": "Llegada1",
        "reloj": reloj,
        "rnd_llegada1": rnd,
        "tiempo_llegada1": llegada,
        "llegada1": llegada + reloj,
        "rnd_llegada2": None,
        "tiempo_llegada2": None,
        "llegada2": anterior["llegada2"],
        "rnd_llegada3": None,
        "tiempo_llegada3": None,
        "llegada3": anterior["llegada3"],
        "id_atendido": id_atendido,
        "rnd_trabajo": rnd_trabajo,
        "duracion_trabajo": duracion_trabajo,
        "rnd_correccion": None,
        "correccion": None,
        "fase": fase,
        "fin_fase": fin_fase,
        "id_suspendido": id_suspendido,
        "restante": restante,
        "restante_fase": restante_fase,
        "estado_mecanografa": estado_mecanografa,
        "cola": anterior["cola"],
        "cola_prioridad": cola_prioridad,
        "ac_espera": anterior["ac_espera"],
        "cont_atendidos": cont_atendidos,
        "ac_tiempo_sistema": anterior["ac_tiempo_sistema"],
        "cont_trabajos": anterior["cont_trabajos"],
        "ultimo_cambio_cola": ultimo_cambio,
        "suma_area_cola": suma_area,
        "trabajos": trabajos,
    }
    return vector

def manejar_llegada(reloj, anterior, numero_directivo):
    trabajos = anterior["trabajos"].copy()
    nuevo_id = len(trabajos) + 1

    rnd = random.random()
    tiempo_llegada = generar_exponencial(MEDIA_LLEGADA, rnd)
    llegada = reloj + tiempo_llegada

    id_atendido = anterior["id_atendido"]
    rnd_trabajo = None
    duracion_trabajo = None

    fase = anterior["fase"]
    fin_fase = anterior["fin_fase"]
    
    cola = anterior["cola"]

    cont_atendidos = anterior["cont_atendidos"]
    ultimo_cambio = anterior["ultimo_cambio_cola"]
    suma_area = anterior["suma_area_cola"]

    if anterior["estado_mecanografa"] == "libre":
        id_atendido = nuevo_id
        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)

        fin_fase = reloj + duracion_trabajo / 2
        fase = "primera mitad"
        
        estado_mecanografa = "ocupada"
        estado_trabajo = "siendo atendido"
        cont_atendidos += 1

    else:
        cola = anterior["cola"] + 1
        estado_mecanografa = anterior["estado_mecanografa"]
        estado_trabajo = "esperando"

    if numero_directivo == 2:
        nombre_evento = "Llegada2"
        rnd_llegada2 = rnd
        tiempo_llegada2 = tiempo_llegada
        llegada2 = llegada
        rnd_llegada3 = None
        tiempo_llegada3 = None
        llegada3 = anterior["llegada3"]
    else:
        nombre_evento = "Llegada3"
        rnd_llegada2 = None
        tiempo_llegada2 = None
        llegada2 = anterior["llegada2"]
        rnd_llegada3 = rnd
        tiempo_llegada3 = tiempo_llegada
        llegada3 = llegada

    if anterior["cola"] + anterior["cola_prioridad"] != cola + anterior["cola_prioridad"]:
        suma_area = anterior["suma_area_cola"] + (reloj - anterior["ultimo_cambio_cola"]) * (anterior["cola"] + anterior["cola_prioridad"])
        ultimo_cambio = reloj

    nuevo_trabajo = {
        "id": nuevo_id,
        "estado": estado_trabajo,
        "llegada": reloj,
        "prioridad": "normal",
        "duracion_trabajo": duracion_trabajo if estado_trabajo == "siendo atendido" else None,
        "fin_correccion": None,
    }

    trabajos.append(nuevo_trabajo)

    vector = {
        "evento": nombre_evento,
        "reloj": reloj,
        "rnd_llegada1": None,
        "tiempo_llegada1": None,
        "llegada1": anterior["llegada1"],
        "rnd_llegada2": rnd_llegada2,
        "tiempo_llegada2": tiempo_llegada2,
        "llegada2": llegada2,
        "rnd_llegada3": rnd_llegada3,
        "tiempo_llegada3": tiempo_llegada3,
        "llegada3": llegada3,
        "id_atendido": id_atendido,
        "rnd_trabajo": rnd_trabajo,
        "duracion_trabajo": duracion_trabajo,
        "rnd_correccion": None,
        "correccion": None,
        "fase": fase,
        "fin_fase": fin_fase,
        "id_suspendido": anterior["id_suspendido"],
        "restante": anterior["restante"],
        "restante_fase": anterior["restante_fase"],
        "estado_mecanografa": estado_mecanografa,
        "cola": cola,
        "cola_prioridad": anterior["cola_prioridad"],
        "ac_espera": anterior["ac_espera"],
        "cont_atendidos": cont_atendidos,
        "ac_tiempo_sistema": anterior["ac_tiempo_sistema"],
        "cont_trabajos": anterior["cont_trabajos"],
        "ultimo_cambio_cola": ultimo_cambio,
        "suma_area_cola": suma_area,
        "trabajos": trabajos,
    }
    return vector

def manejar_chequeo_correccion(reloj, anterior, id_atendido):
    trabajos = anterior["trabajos"].copy()
    rnd_correccion = random.random()
    correcion = rnd_correccion < PROBA_CORRECCION
    
    if correcion:
        fase = "correccion"
        fin_fase = reloj + TIEMPO_CORRECCION
        trabajos[id_atendido - 1]["estado"] = "siendo corregido"
        if anterior["estado_mecanografa"] == "ocupada 1":
            estado_mecanografa = "esperando correccion 1"
        else:
            estado_mecanografa = "esperando correccion"
    else:
        fase = "segunda mitad"
        duracion_trabajo = trabajos[id_atendido - 1]["duracion_trabajo"]
        fin_fase = reloj + duracion_trabajo / 2
        estado_mecanografa = anterior["estado_mecanografa"]

    vector = {
        "evento": "Chequeo correccion",
        "reloj": reloj,
        "rnd_llegada1": None,
        "tiempo_llegada1": None,
        "llegada1": anterior["llegada1"],
        "rnd_llegada2": None,
        "tiempo_llegada2": None,
        "llegada2": anterior["llegada2"],
        "rnd_llegada3": None,
        "tiempo_llegada3": None,
        "llegada3": anterior["llegada3"],
        "id_atendido": id_atendido,
        "rnd_trabajo": None,
        "duracion_trabajo": None,
        "rnd_correccion": rnd_correccion,
        "correccion": correcion,
        "fase": fase,
        "fin_fase": fin_fase,
        "id_suspendido": anterior["id_suspendido"],
        "restante": anterior["restante"],
        "restante_fase": anterior["restante_fase"],
        "estado_mecanografa": estado_mecanografa,
        "cola": anterior["cola"],
        "cola_prioridad": anterior["cola_prioridad"],
        "ac_espera": anterior["ac_espera"],
        "cont_atendidos": anterior["cont_atendidos"],
        "ac_tiempo_sistema": anterior["ac_tiempo_sistema"],
        "cont_trabajos": anterior["cont_trabajos"],
        "ultimo_cambio_cola": anterior["ultimo_cambio_cola"],
        "suma_area_cola": anterior["suma_area_cola"],
        "trabajos": trabajos,
    }
    return vector

def manejar_fin_correccion(reloj, anterior, id_atendido):
    trabajos = anterior["trabajos"].copy()
    trabajos[id_atendido - 1]["estado"] = "corregido"
    fase = "segunda mitad"
    fin_fase = reloj + trabajos[id_atendido - 1]["duracion_trabajo"] / 2

    if anterior["estado_mecanografa"] == "esperando correccion 1":
        estado_mecanografa = "ocupada 1"
    else:
        estado_mecanografa = "ocupada"
    
    vector = {
        "evento": "Fin correccion activo",
        "reloj": reloj,
        "rnd_llegada1": None,
        "tiempo_llegada1": None,
        "llegada1": anterior["llegada1"],
        "rnd_llegada2": None,
        "tiempo_llegada2": None,
        "llegada2": anterior["llegada2"],
        "rnd_llegada3": None,
        "tiempo_llegada3": None,
        "llegada3": anterior["llegada3"],
        "id_atendido": id_atendido,
        "rnd_trabajo": None,
        "duracion_trabajo": None,
        "rnd_correccion": None,
        "correccion": None,
        "fase": fase,
        "fin_fase": fin_fase,
        "id_suspendido": anterior["id_suspendido"],
        "restante": anterior["restante"],
        "restante_fase": anterior["restante_fase"],
        "estado_mecanografa": estado_mecanografa,
        "cola": anterior["cola"],
        "cola_prioridad": anterior["cola_prioridad"],
        "ac_espera": anterior["ac_espera"],
        "cont_atendidos": anterior["cont_atendidos"],
        "ac_tiempo_sistema": anterior["ac_tiempo_sistema"],
        "cont_trabajos": anterior["cont_trabajos"],
        "ultimo_cambio_cola": anterior["ultimo_cambio_cola"],
        "suma_area_cola": anterior["suma_area_cola"],
        "trabajos": trabajos,
    }
    return vector

def manejar_fin_correcion_suspendido(reloj, anterior, id):
    trabajos = anterior["trabajos"].copy()
    trabajos[id - 1]["estado"] = "suspendido"
    trabajos[id - 1]["fin_correccion"] = None

    restante = trabajos[id - 1]["duracion_trabajo"] / 2
    restante_fase = "segunda mitad"

    vector = {
        "evento": "Fin correccion suspendido",
        "reloj": reloj,
        "rnd_llegada1": None,
        "tiempo_llegada1": None,
        "llegada1": anterior["llegada1"],
        "rnd_llegada2": None,
        "tiempo_llegada2": None,
        "llegada2": anterior["llegada2"],
        "rnd_llegada3": None,
        "tiempo_llegada3": None,
        "llegada3": anterior["llegada3"],
        "id_atendido": anterior["id_atendido"],
        "rnd_trabajo": None,
        "duracion_trabajo": None,
        "rnd_correccion": None,
        "correccion": None,
        "fase": anterior["fase"],
        "fin_fase": anterior["fin_fase"],
        "id_suspendido": anterior["id_suspendido"],
        "restante": restante,
        "restante_fase": restante_fase,
        "estado_mecanografa": anterior["estado_mecanografa"],
        "cola": anterior["cola"],
        "cola_prioridad": anterior["cola_prioridad"],
        "ac_espera": anterior["ac_espera"],
        "cont_atendidos": anterior["cont_atendidos"],
        "ac_tiempo_sistema": anterior["ac_tiempo_sistema"],
        "cont_trabajos": anterior["cont_trabajos"],
        "ultimo_cambio_cola": anterior["ultimo_cambio_cola"],
        "suma_area_cola": anterior["suma_area_cola"],
        "trabajos": trabajos,
    }
    return vector

def manejar_fin_servicio(reloj, anterior, id_atendido):
    trabajos = anterior["trabajos"].copy()
    trabajos[id_atendido - 1]["estado"] = "finalizado"

    rnd_trabajo = None
    duracion_trabajo = None

    id_suspendido = anterior["id_suspendido"]
    restante = anterior["restante"]
    restante_fase = anterior["restante_fase"]
    cola = anterior["cola"]
    cola_prioridad = anterior["cola_prioridad"]

    ac_espera = anterior["ac_espera"]
    tiempo_sistema = reloj - trabajos[id_atendido - 1]["llegada"]
    cont_atendidos = anterior["cont_atendidos"]
    ac_tiempo_sistema = anterior["ac_tiempo_sistema"] + tiempo_sistema
    cont_trabajos = anterior["cont_trabajos"] + 1

    ultimo_cambio = anterior["ultimo_cambio_cola"]
    suma_area = anterior["suma_area_cola"]

    if anterior["cola_prioridad"] > 0:
        nueva_id = None
        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)
        fin_fase = reloj + duracion_trabajo / 2

        for t in trabajos:
            if t["estado"] == "esperando" and t["prioridad"] == "especial":
                nueva_id = t["id"]
                t["estado"] = "siendo atendido"
                t["duracion_trabajo"] = duracion_trabajo
                break

        if nueva_id is None:
            estado_mecanografa = "libre"
            fase = None
            fin_fase = None
        else:
            fase = "primera mitad"
            estado_mecanografa = "ocupada 1"
            espera = reloj - trabajos[nueva_id - 1]["llegada"]
            ac_espera = anterior["ac_espera"] + espera
            cont_atendidos += 1
        
        cola_prioridad = anterior["cola_prioridad"] - 1

    elif anterior["id_suspendido"] is not None:
        nueva_id = anterior["id_suspendido"]
        id_suspendido = None
        restante = None
        restante_fase = None

        if anterior["restante_fase"] == "correcion":
            trabajos[anterior["id_suspendido"] - 1]["fin_correccion"] = None
            fase = "correccion"
            fin_fase = reloj + TIEMPO_CORRECCION
            estado_mecanografa = "esperando correccion"
        else:
            trabajos[anterior["id_suspendido"] - 1]["estado"] = "siendo atendido"
            fase = anterior["restante_fase"]
            fin_fase = reloj + anterior["restante"]
            estado_mecanografa = "ocupada"

    elif anterior["cola"] > 0:
        nueva_id = None
        rnd_trabajo = random.random()
        duracion_trabajo = generar_uniforme(A, B, rnd_trabajo)
        fin_fase = reloj + duracion_trabajo / 2
        
        for t in trabajos:
            if t["estado"] == "esperando" and t["prioridad"] == "normal":
                nueva_id = t["id"]
                t["estado"] = "siendo atendido"
                t["duracion_trabajo"] = duracion_trabajo
                break

        if nueva_id is None:
            estado_mecanografa = "libre"
            fase = None
            fin_fase = None
        else:
            fase = "primera mitad"
            estado_mecanografa = "ocupada"
            espera = reloj - trabajos[nueva_id - 1]["llegada"]
            ac_espera = anterior["ac_espera"] + espera
            cont_atendidos += 1
        
        cola = anterior["cola"] - 1
        cola_prioridad = anterior["cola_prioridad"]

    else:
        estado_mecanografa = "libre"
        nueva_id = None
        rnd_trabajo = None
        duracion_trabajo = None
        fase = None
        fin_fase = None

    if anterior["cola"] + anterior["cola_prioridad"] != cola + cola_prioridad:
        suma_area = anterior["suma_area_cola"] + (reloj - anterior["ultimo_cambio_cola"]) * (anterior["cola"] + anterior["cola_prioridad"])
        ultimo_cambio = reloj

    vector = {
        "evento": "Fin servicio",
        "reloj": reloj,
        "rnd_llegada1": None,
        "tiempo_llegada1": None,
        "llegada1": anterior["llegada1"],
        "rnd_llegada2": None,
        "tiempo_llegada2": None,
        "llegada2": anterior["llegada2"],
        "rnd_llegada3": None,
        "tiempo_llegada3": None,
        "llegada3": anterior["llegada3"],
        "id_atendido": nueva_id,
        "rnd_trabajo": rnd_trabajo,
        "duracion_trabajo": duracion_trabajo,
        "rnd_correccion": None,
        "correccion": None,
        "fase": fase,
        "fin_fase": fin_fase,
        "id_suspendido": id_suspendido,
        "restante": restante,
        "restante_fase": restante_fase,
        "estado_mecanografa": estado_mecanografa,
        "cola": cola,
        "cola_prioridad": cola_prioridad,
        "ac_espera": ac_espera,
        "cont_atendidos": cont_atendidos,
        "ac_tiempo_sistema": ac_tiempo_sistema,
        "cont_trabajos": cont_trabajos,
        "ultimo_cambio_cola": ultimo_cambio,
        "suma_area_cola": suma_area,
        "trabajos": trabajos
    }
    return vector
