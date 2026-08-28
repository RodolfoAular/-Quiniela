import models

def cerrar_partido(
    db,
    partido,
    goles_local,
    goles_visitante,
#   fecha_hora,
   finalizado,
#    winner,
    
    
):
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
  # partido.fecha_hora = fecha_hora
    partido.finalizado = finalizado
 #   partido.winner = winner
    

    if partido.finalizado:
        pronosticos = db.query(models.Pronostico).filter(
            models.Pronostico.partido_id == partido.id
        ).all()

        resultado_real = "empate"
        if partido.goles_local > partido.goles_visitante:
            resultado_real = "local"
        elif partido.goles_visitante > partido.goles_local:
            resultado_real = "visitante"

        for pronostico in pronosticos:
            puntos_ganados = 0

            resultado_pronostico = "empate"
            if pronostico.goles_local > pronostico.goles_visitante:
                resultado_pronostico = "local"
            elif pronostico.goles_visitante > pronostico.goles_local:
                resultado_pronostico = "visitante"

            if (
                pronostico.goles_local == partido.goles_local
                and pronostico.goles_visitante == partido.goles_visitante
            ):
                puntos_ganados = 3
            elif resultado_pronostico == resultado_real:
                puntos_ganados = 1

            if puntos_ganados > 0:
                pronostico.puntos_obtenidos = puntos_ganados
                pronostico.usuario.puntos_totales += puntos_ganados

        # Propagación a slots SOLO cuando el partido está finalizado
        ganador_id = None
        perdedor_id = None
        if partido.goles_local > partido.goles_visitante:
            ganador_id = partido.equipo_local_id
            perdedor_id = partido.equipo_visitante_id
        elif partido.goles_visitante > partido.goles_local:
            ganador_id = partido.equipo_visitante_id
            perdedor_id = partido.equipo_local_id

        if ganador_id is not None:
            slots = db.query(models.Slot).filter(
                models.Slot.source_partido_id == partido.id
            ).all()

            for s in slots:
                # Si el slot trae equipo fijo, tiene prioridad
                if s.fixed_equipo_id is not None:
                    equipo_a_asignar = s.fixed_equipo_id
                else:
                    equipo_a_asignar = ganador_id if s.source_type == "ganador" else perdedor_id

                if equipo_a_asignar is None:
                    continue

                if s.position == "local":
                    if s.target_partido.equipo_local_id is None:
                        s.target_partido.equipo_local_id = equipo_a_asignar
                elif s.position == "visitante":
                    if s.target_partido.equipo_visitante_id is None:
                        s.target_partido.equipo_visitante_id = equipo_a_asignar

    db.commit()
    db.refresh(partido)
    return partido

def administrar_partido(db, partido, datos):

    if datos.fecha_hora:
        partido.fecha_hora = datos.fecha_hora


    if datos.goles_local is not None:
        partido.goles_local = datos.goles_local


    if datos.goles_visitante is not None:
        partido.goles_visitante = datos.goles_visitante


    if datos.finalizado is not None:
        partido.finalizado = datos.finalizado


    if datos.winner is not None:
        partido.winner = datos.winner

    if datos.finalizado is True:
        cerrar_partido(db, partido, partido.goles_local, partido.goles_visitante, partido.finalizado)

    if datos.finalizado is False:    
        db.commit()
