from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import models
import schemas
from seacher import Actualizacion_Periodica
from marcador import cerrar_partido, administrar_partido
from database import engine, get_db, SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler # type: ignore[reportMissingImports]

scheduler = BackgroundScheduler()

# Crea las tablas en la base de datos PostgreSQL si no existen
models.Base.metadata.create_all(bind = engine)
Actualizacion_automatica = True

app  =  FastAPI(
    title = "API Quiniela Mundial",
    description = "Backend para la gestión de quinielas del mundial (hasta 20 personas).",
    version = "1.0.0"
)

# ==========================================
# RUTAS DE USUARIOS (Jugadores)
# ==========================================
@app.post("/usuarios/", response_model = schemas.Usuario, tags = ["Usuarios"])
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = models.Usuario(nombre = usuario.nombre, es_admin = usuario.es_admin)
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@app.get("/usuarios/posiciones", response_model = List[schemas.Usuario], tags = ["Usuarios"])
def tabla_posiciones(db: Session = Depends(get_db)):
    # Devuelve los usuarios ordenados por puntos de mayor a menor (máximo 20 personas)
    usuarios = db.query(models.Usuario).order_by(models.Usuario.puntos_totales.desc()).limit(20).all()
    return usuarios


# ==========================================
# RUTAS DE EQUIPOS
# ==========================================
@app.post("/equipos/", response_model = schemas.Equipo, tags = ["Equipos"])
def crear_equipo(equipo: schemas.EquipoCreate, db: Session = Depends(get_db)):
    db_equipo = models.Equipo(**equipo.model_dump())
    db.add(db_equipo)
    db.commit()
    db.refresh(db_equipo)
    return db_equipo

@app.get("/equipos/", response_model = List[schemas.Equipo], tags = ["Equipos"])
def listar_equipos(db: Session = Depends(get_db)):
    return db.query(models.Equipo).all()


# ==========================================
# RUTAS DE PARTIDOS
# ==========================================

@app.post("/partidos/", response_model=schemas.Partido, tags=["Partidos"])
def crear_partido(partido: schemas.PartidoCreate, db: Session = Depends(get_db)):

    # Si ambos equipos vienen definidos, no pueden ser el mismo
    if (
        partido.equipo_local_id is not None
        and partido.equipo_visitante_id is not None
        and partido.equipo_local_id == partido.equipo_visitante_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Un equipo no puede jugar contra sí mismo"
        )

    # Si viene equipo local, validar que exista
    if partido.equipo_local_id is not None:
        local = db.query(models.Equipo).filter(
            models.Equipo.id == partido.equipo_local_id
        ).first()
        if not local:
            raise HTTPException(status_code=404, detail="Equipo local no existe")

    # Si viene equipo visitante, validar que exista
    if partido.equipo_visitante_id is not None:
        visitante = db.query(models.Equipo).filter(
            models.Equipo.id == partido.equipo_visitante_id
        ).first()
        if not visitante:
            raise HTTPException(status_code=404, detail="Equipo visitante no existe")

    db_partido = models.Partido(**partido.model_dump())
    db.add(db_partido)
    db.commit()
    db.refresh(db_partido)

    return db_partido

@app.get("/partidos/", response_model = List[schemas.Partido], tags = ["Partidos"])
def listar_partidos(db: Session = Depends(get_db)):
    return db.query(models.Partido).all()


# ==========================================
# RUTAS DE PRONÓSTICOS (Quiniela)
# ==========================================
@app.post("/pronosticos/", response_model = schemas.Pronostico, tags = ["Pronosticos"])
def crear_pronostico(pronostico: schemas.PronosticoCreate, db: Session = Depends(get_db)):

    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == pronostico.usuario_id
    ).first()

    if not usuario:
        raise HTTPException(
            status_code = 404,
            detail="Usuario no encontrado"
        )

    partido = db.query(models.Partido).filter(
        models.Partido.id == pronostico.partido_id
    ).first()

    if not partido:
        raise HTTPException(
            status_code = 404,
            detail = "Partido no encontrado"
        )

    if partido.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code = 400,
            detail="El partido ya comenzó, no se aceptan más pronósticos"
        )

    pronostico_previo = db.query(models.Pronostico).filter(
        models.Pronostico.usuario_id == pronostico.usuario_id,
        models.Pronostico.partido_id == pronostico.partido_id
    ).first()

    if pronostico_previo:
        raise HTTPException(
            status_code = 400,
            detail="El usuario ya tiene un pronóstico para este partido"
        )

    db_pronostico = models.Pronostico(
        **pronostico.model_dump()
    )

    db.add(db_pronostico)
    db.commit()
    db.refresh(db_pronostico)

    return db_pronostico



# @app.put("/partidos/{partido_id}/resultado", response_model=schemas.Partido, tags = ["Partidos"])
# def actualizar_resultado_partido(
#     partido_id: int,
#     resultado: schemas.UpdatePartidoAdmin,
#     admin_id: int,
#     db: Session = Depends(get_db)
# ):
#     admin = db.query(models.Usuario).filter(models.Usuario.id == admin_id).first()
#     if not admin or not admin.es_admin:
#         raise HTTPException(
#             status_code = 403,
#             detail = "No tienes permisos de administrador para realizar esta acción"
#         )

#     partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
#     if not partido:
#         raise HTTPException(status_code = 404, detail="Partido no encontrado")


#     # Para cerrar partido, ambos equipos deben estar definidos
#     if partido.equipo_local_id is None or partido.equipo_visitante_id is None:
#         raise HTTPException(
#             status_code = 400,
#             detail = "No se puede finalizar un partido sin equipos definidos"
#         )
    
#     Resultado_Partido = [-1,0,1,2]
#     if resultado.winner not in Resultado_Partido:
#         raise HTTPException(
#         status_code = 400,
#         detail="Winner inválido"
#         )

#     return cerrar_partido(
#     db,
#     partido,
#     resultado.goles_local,
#     resultado.goles_visitante,
#     #resultado.fecha_hora,
#     #resultado.finalizado,
#     resultado.winner

#     )
    

@app.post("/auditar-promiedos", tags=["Promiedos"])
def auditar_promiedos(
    admin_id: int,
    db: Session = Depends(get_db)
):

    admin = db.query(models.Usuario).filter(
        models.Usuario.id == admin_id
    ).first()

    if not admin or not admin.es_admin:

        raise HTTPException(
            status_code = 403,
            detail="No tienes permisos de administrador"
        )

    print("ENTRE AL ENDPOINT")

    actualizados, creados = Actualizacion_Periodica(db)

    return {"mensaje": "Auditoría completada", "partidos_actualizados": actualizados, "partidos_creados": creados}

def tarea_programada():
    global Actualizacion_automatica

    if not Actualizacion_automatica:
        print("Actualización automática desactivada")
        return
    
    db = SessionLocal()

    try:
        Actualizacion_Periodica(db)

    finally:
        db.close()

scheduler.add_job(
    tarea_programada,
    "interval",
    seconds = 10
)
scheduler.start()

@app.put("/admin/partido/{partido_id}", response_model=schemas.Partido)
def modificar_partido(
    partido_id: int,
    admin_id: int,
    datos: schemas.UpdatePartidoAdmin,
    db: Session = Depends(get_db)
):

    admin = db.query(models.Usuario).filter(
    models.Usuario.id == admin_id,
    models.Usuario.es_admin == True
    ).first()
    
    if not admin:
        raise HTTPException(status_code = 403, detail = "No autorizado")
    
    partido = db.query(models.Partido).filter(
        models.Partido.id == partido_id
    ).first()


    if not partido:
        raise HTTPException(status_code = 404, detail="Partido no encontrado")
    
    administrar_partido(db, partido, datos)

    return partido

@app.put("/cambio-modo")
def cambio_modo(
    datos: schemas.CambioModo,
    admin_id: int,
    db: Session = Depends(get_db)
):
    
        admin = db.query(models.Usuario).filter(
        models.Usuario.id == admin_id,
        models.Usuario.es_admin == True
    ).first()

        if not admin:

            raise HTTPException(status_code = 403, detail = "No autorizado")
        
        permisos = db.query(models.PermisosAdmin).first()

        if permisos is None:
        
            permisos = models.PermisosAdmin(actualizacion_automatica = datos.actualizacion_automatica)
        else:

            permisos.actualizacion_automatica = datos.actualizacion_automatica

        db.add(permisos)

        db.commit()

        return {"mensaje": "Modo actualizado", "actualizacion_automatica": permisos.actualizacion_automatica}

@app.get("/")
async def root():
    return {"status": "Proceso PID 1 activo", "infraestructura": "FastAPI + Uvicorn"}
