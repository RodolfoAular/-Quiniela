import httpx # type: ignore[reportMissingImports]
from datetime import datetime
from sqlalchemy.orm import Session
import models
from marcador import cerrar_partido
from database import engine, get_db, SessionLocal

def obtener_datos_promiedos():

    # league/tables_and_fixtures/fjda
    # league/games/fjda/5930_25_3_-1
    # league/games/fjda/5930_25_1_1
    # league/games/fjda/5930_25_1_2
    # league/games/fjda/5930_25_4_-1

    url = (
        "https://api.promiedos.com.ar/"
        "league/games/fjda/5930_25_4_-1"
    )

    respuesta = httpx.get(
        url,
        timeout=10.0
    )

    respuesta.raise_for_status()
    datos = respuesta.json()
    partidos = []

    
    print("hola")
    print("TOTAL PARTIDOS:", len(datos["games"]))
   
    for game in datos["games"]:

        scores = game.get("scores")
        winner = game.get("winner")

        if scores is not None:
            goles_local = int(scores[0])
            goles_visitante = int(scores[1])
        else:
            goles_local = None
            goles_visitante = None

            

        partidos.append({

            "promiedos_id": game["id"],
            
            "equipo_local_id": game["teams"][0]["country_id"],
            "equipo_visitante_id": game["teams"][1]["country_id"],

            "equipo_local": game["teams"][0]["name"],
            "equipo_visitante": game["teams"][1]["name"],
            
            "goles_local": goles_local,
            "goles_visitante": goles_visitante,

            "finalizado": game["status"]["name"] == "Finalizado",

            "winner": winner,

            "fecha": game["start_time"]

        })

    return partidos

def auditar_marcadores():

    print("AUDITORIA INICIADA")

    partidos_promiedos = obtener_datos_promiedos()

    print(
        "Partidos encontrados:",
        len(partidos_promiedos)
    )

    return partidos_promiedos


def Actualizacion_Periodica(db: Session):

    permisos = db.query(models.PermisosAdmin).first()

    if permisos and not permisos.actualizacion_automatica:

        print("ACTUALIZACIÓN AUTOMÁTICA DESACTIVADA")

        return [], 0

    print("AUDITORIA INICIADA")

    actualizados = auditar_marcadores()

    creados = 0
    
    for datos in actualizados:

        partido = db.query(models.Partido).filter(
            models.Partido.promiedos_id == datos["promiedos_id"],
        ).first()

        if partido is not None:

            partido.goles_local = datos["goles_local"]
            partido.goles_visitante = datos["goles_visitante"]

            partido.fecha_hora = datetime.strptime(
                datos["fecha"],
                "%d-%m-%Y %H:%M"
            )

            partido.winner = datos["winner"]
            

            if (not partido.finalizado and datos["finalizado"]):
     
                partido.finalizado = datos["finalizado"]

                cerrar_partido(db, partido)

            continue


        print(
            "CREANDO PARTIDO NUEVO:",
            datos["equipo_local"],
            datos["equipo_local"]
        )
        equipo_local = db.query(models.Equipo).filter(
            models.Equipo.nombre == datos["equipo_local"]
        ).first()

        equipo_visitante = db.query(models.Equipo).filter(
            models.Equipo.nombre == datos["equipo_visitante"]
        ).first()

        if equipo_local is None or equipo_visitante is None:

            print(
                f"No existen los equipos "
                f"{datos['equipo_local']} vs "
                f"{datos['equipo_visitante']}"
            )

            continue

        fecha = datetime.strptime(
            datos["fecha"],
            "%d-%m-%Y %H:%M"
        )

        nuevo_partido = models.Partido(

            promiedos_id = datos["promiedos_id"],

            equipo_local_id = equipo_local.id,
            equipo_visitante_id = equipo_visitante.id,

            fase = "Fase de grupos",

            goles_local = datos["goles_local"],
            goles_visitante = datos["goles_visitante"],
            
            fecha_hora = fecha,
            
            finalizado = (datos["finalizado"]),

            winner = datos["winner"]

        )

        db.add(nuevo_partido)

        creados += 1

    db.commit()

    return actualizados, creados