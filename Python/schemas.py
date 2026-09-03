from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
import main

# ==========================================
# 1. ESQUEMAS DE EQUIPOS (Teams)
# ==========================================
class EquipoBase(BaseModel):
    nombre: str
    grupo: str
    codigo_pais: Optional[str] = Field(default=None, max_length=3)

class EquipoCreate(EquipoBase):
    pass

class Equipo(EquipoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. ESQUEMAS DE PARTIDOS
# ==========================================
class PartidoBase(BaseModel):
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None
    fecha_hora: datetime
    fase: str
    winner: int = 0

    promiedos_id: Optional[str] = None

class PartidoCreate(PartidoBase):
    pass


class UpdatePartidoAdmin(BaseModel):
    goles_local: Optional[int] = Field(default = None, ge=0)
    goles_visitante: Optional[int] = Field(default = None, ge=0)
    fecha_hora: Optional[datetime] = None
    winner: Optional[int] = None 
    fase: Optional[str] = None
    finalizado: Optional[bool] = None

class Partido(PartidoBase):
    id: int
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None
    finalizado: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. ESQUEMAS DE PRONÓSTICOS
# ==========================================
class PronosticoBase(BaseModel):
    partido_id: int
    goles_local: int = Field(ge=0)
    goles_visitante: int = Field(ge=0)

class PronosticoCreate(PronosticoBase):
    usuario_id: int

class Pronostico(PronosticoBase):
    id: int
    usuario_id: int
    puntos_obtenidos: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. ESQUEMAS DE USUARIOS
# ==========================================
class UsuarioBase(BaseModel):
    nombre: str
    es_admin: bool = False

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id: int
    activo: bool = True
    puntos_totales: int = 0

    model_config = ConfigDict(from_attributes=True)

# =======================================
# 5. ESQUEMAS DE SLOTS
# =======================================

class SlotBase(BaseModel):
    source_partido_id: int
    target_partido_id: int
    position: str  # 'local'|'visitante'
    source_type: str  # 'ganador'|'perdedor'
    fixed_equipo_id: Optional[int] = None

class SlotCreate(SlotBase):
    pass

class Slot(SlotBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CambioModo(BaseModel):
    actualizacion_automatica: bool