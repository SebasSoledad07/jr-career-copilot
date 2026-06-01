from typing import List, Optional
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    """
    Representa la información de contacto estructurada del ingeniero junior.
    """
    email: Optional[str] = Field(None, description="Email address of the junior engineer")
    phone: Optional[str] = Field(None, description="Phone number of the junior engineer")
    location: Optional[str] = Field(None, description="Physical location or city and country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")

class OptimizedExperience(BaseModel):
    """
    Representa una experiencia profesional optimizada para la oferta laboral.
    """
    company: str = Field(description="Name of the company or organization")
    role: str = Field(description="Optimized role title aligned with the job description")
    period: str = Field(description="Employment or project period")
    tailored_achievements: List[str] = Field(
        description="Action-oriented, high-impact achievements tailored to the target job description. Focus on metrics, technologies, and results without inventing any facts."
    )

class OptimizedEducation(BaseModel):
    """
    Representa la formación académica u proyectos de estudio optimizados.
    """
    institution: str = Field(description="Name of the educational institution")
    degree: str = Field(description="Degree name or certification")
    period: str = Field(description="Period of study or completion date")
    achievements: List[str] = Field(
        description="Key academic achievements, coursework, or project descriptions aligned with the job requirements."
    )

class OptimizedCV(BaseModel):
    """
    Estructura completa del currículum optimizado y adaptado.
    """
    full_name: str = Field(description="Full name of the junior engineer")
    contact_info: ContactInfo = Field(description="Structured contact info of the junior engineer")
    professional_summary: str = Field(
        description="A powerful 3-4 sentence professional summary tailored to the target job using the Pygmalion Effect, highlighting technical capability and potential."
    )
    optimized_skills: List[str] = Field(
        description="List of core technical and professional skills filtered and sorted by relevance to the job description."
    )
    experiences: List[OptimizedExperience] = Field(
        description="List of professional experiences with achievements tailored using action verbs and technical keywords."
    )
    education: List[OptimizedEducation] = Field(
        description="List of education details and tailored academic projects."
    )


# ─── Modelos para el Robustness Judge ─────────────────────────────────────────

class Alucinacion(BaseModel):
    """
    Representa una alucinación detectada en el CV optimizado:
    un dato fabricado, exagerado o que no existe en el perfil original.
    """
    campo: str = Field(
        description="Campo del CV donde se detectó la alucinación (e.g., 'skills', 'experiences[0].achievements', 'professional_summary')."
    )
    valor_original: Optional[str] = Field(
        None,
        description="Valor que aparece en el perfil original del candidato para ese campo, o null si el campo fue completamente fabricado."
    )
    valor_generado: str = Field(
        description="Valor generado por la IA que se considera alucinación."
    )
    tipo: str = Field(
        description="Tipo de alucinación: 'fabricacion' (dato inventado que no existe en el perfil), 'exageracion' (dato real inflado o distorsionado), 'atribucion_falsa' (logro o tecnología atribuida incorrectamente)."
    )
    severidad: str = Field(
        description="Nivel de severidad: 'critica' (dato completamente falso), 'alta' (exageración significativa), 'media' (exageración menor), 'baja' (imprecisión sutil)."
    )
    explicacion: str = Field(
        description="Explicación detallada de por qué este dato se considera una alucinación y el impacto potencial."
    )


class Inconsistencia(BaseModel):
    """
    Representa una inconsistencia lógica o factual detectada en el CV optimizado
    (fechas que no cuadran, roles contradictorios, etc.).
    """
    campo_afectado: str = Field(
        description="Campo o sección del CV donde se detectó la inconsistencia."
    )
    descripcion: str = Field(
        description="Descripción clara de la inconsistencia encontrada."
    )
    severidad: str = Field(
        description="Nivel de severidad: 'critica', 'alta', 'media', 'baja'."
    )


class ValidacionEtica(BaseModel):
    """
    Resultado de un criterio de validación ética sobre el CV optimizado.
    """
    criterio: str = Field(
        description="Nombre del criterio ético evaluado (e.g., 'No fabricación de títulos', 'No inflación de métricas', 'Veracidad de certificaciones')."
    )
    cumple: bool = Field(
        description="True si el CV cumple con este criterio ético, False si lo viola."
    )
    detalle: str = Field(
        description="Explicación de cómo se evaluó este criterio y evidencia encontrada."
    )


class ReporteRobustez(BaseModel):
    """
    Reporte completo de validación de robustez del CV optimizado.
    Evalúa alucinaciones, inconsistencias y compliance ético.
    """
    puntuacion_general: float = Field(
        description="Puntuación de robustez del 0.0 al 10.0 donde 10 es perfecto (sin alucinaciones ni problemas)."
    )
    veredicto: str = Field(
        description="Veredicto general: 'APROBADO' (score >= 7), 'APROBADO_CON_OBSERVACIONES' (score >= 5), 'RECHAZADO' (score < 5)."
    )
    resumen_ejecutivo: str = Field(
        description="Resumen ejecutivo de 2-3 oraciones sobre la calidad general del CV optimizado."
    )
    total_alucinaciones: int = Field(
        description="Número total de alucinaciones detectadas."
    )
    alucinaciones: List[Alucinacion] = Field(
        description="Lista detallada de todas las alucinaciones encontradas."
    )
    total_inconsistencias: int = Field(
        description="Número total de inconsistencias detectadas."
    )
    inconsistencias: List[Inconsistencia] = Field(
        description="Lista detallada de inconsistencias lógicas o factuales encontradas."
    )
    validacion_etica: List[ValidacionEtica] = Field(
        description="Resultados de cada criterio de validación ética evaluado."
    )
    recomendaciones: List[str] = Field(
        description="Lista de recomendaciones concretas para corregir los problemas detectados."
    )
