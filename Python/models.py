from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import UniqueConstraint

# Base de la cual heredarán todos nuestros modelos
Base = declarative_base()

# ==========================================
# 1. MODELO DE USUARIOS (Jugadores de la quiniela)
# ==========================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    es_admin = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    puntos_totales = Column(Integer, default=0)

    # Relación uno-a-muchos: un usuario tiene muchos pronósticos
    pronosticos = relationship("Pronostico", back_populates="usuario", cascade="all, delete-orphan")


# ==========================================
# 2. MODELO DE EQUIPOS (Selecciones)
# ==========================================
class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    grupo = Column(String(20), nullable=False)
    codigo_pais = Column(String(3), unique=True, index=True, nullable=True)

    # Se definen relaciones inversas para los partidos como local y visitante
    partidos_local = relationship("Partido", foreign_keys="[Partido.equipo_local_id]", back_populates="equipo_local")
    partidos_visitante = relationship("Partido", foreign_keys="[Partido.equipo_visitante_id]", back_populates="equipo_visitante")


# ==========================================
# 3. MODELO DE PARTIDOS (Enfrentamientos del mundial)
# ==========================================
class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True, index=True)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"), nullable=True)
    equipo_visitante_id = Column(Integer, ForeignKey("equipos.id"), nullable=True)
    fecha_hora = Column(DateTime, nullable=False)
    fase = Column(String(50), nullable=False)
    goles_local = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    finalizado = Column(Boolean, default=False)
    winner = Column(Integer, nullable = False)
    promiedos_id = Column(String(20), nullable=True, unique=True, index=True)

    # Relaciones con el modelo de Equipo
    equipo_local = relationship("Equipo", foreign_keys=[equipo_local_id], back_populates="partidos_local")
    equipo_visitante = relationship("Equipo", foreign_keys=[equipo_visitante_id], back_populates="partidos_visitante")
    
    # Relación uno-a-muchos: un partido recibe muchos pronósticos
    pronosticos = relationship("Pronostico", back_populates="partido", cascade="all, delete-orphan")

    
# ==========================================
# 4. MODELO DE PRONÓSTICOS (Quiniela de los usuarios)
# ==========================================
class Pronostico(Base):
    __tablename__ = "pronosticos"
    __table_args__ = (
        UniqueConstraint("usuario_id", "partido_id", name="uq_usuario_partido"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    
    # Goles pronosticados por el usuario
    goles_local = Column(Integer, nullable=False)
    goles_visitante = Column(Integer, nullable=False)
    
    # Puntos que se otorgan una vez que el partido finaliza
    puntos_obtenidos = Column(Integer, default=0)

    # Relaciones de pertenencia
    usuario = relationship("Usuario", back_populates="pronosticos")
    partido = relationship("Partido", back_populates="pronosticos")

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    source_partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    target_partido_id = Column(Integer, ForeignKey("partidos.id"), nullable=False, index=True)
    position = Column(String(10), nullable=False)  # 'local' o 'visitante'
    source_type = Column(String(10), nullable=False)  # 'ganador' o 'perdedor'
    fixed_equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=True)

    source_partido = relationship("Partido", foreign_keys=[source_partido_id])
    target_partido = relationship("Partido", foreign_keys=[target_partido_id])
    fixed_equipo = relationship("Equipo", foreign_keys=[fixed_equipo_id])

class PermisosAdmin(Base):
    __tablename__ = "permisos_admin"

    id = Column(Integer, primary_key=True, index=True)

    actualizacion_automatica = Column(Boolean, default=True, nullable=False)