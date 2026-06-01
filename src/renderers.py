import os
import sys
import jinja2
from models import OptimizedCV

# Diccionario de traducción para las cabeceras del currículum según el idioma seleccionado
HEADERS = {
    "es": {
        "summary": "Resumen Profesional",
        "skills": "Habilidades y Tecnologías",
        "skills_label": "Competencias clave",
        "experience": "Proyectos Destacados y Experiencia Práctica",
        "education": "Educación y Formación",
        "footer": "Currículum optimizado automáticamente utilizando Inteligencia Artificial (Gemini 2.5 Flash)."
    },
    "en": {
        "summary": "Professional Summary",
        "skills": "Skills & Technologies",
        "skills_label": "Key competencies",
        "experience": "Projects & Practical Experience",
        "education": "Education & Training",
        "footer": "Resume automatically optimized using Artificial Intelligence (Gemini 2.5 Flash)."
    }
}

def generate_markdown(cv: OptimizedCV, lang: str = "es") -> str:
    """
    Convierte el modelo de datos de OptimizedCV en un currículum con formato Markdown elegante y legible.
    
    Args:
        cv (OptimizedCV): El CV optimizado devuelto por Gemini.
        lang (str): Idioma de salida ('es' o 'en').
        
    Returns:
        str: El contenido del currículum con formato Markdown listo para guardarse.
    """
    headers = HEADERS.get(lang, HEADERS["es"])
    
    # Construir la cabecera de contacto
    contact = cv.contact_info
    contact_parts = []
    if contact.email:
        contact_parts.append(f"📧 [{contact.email}](mailto:{contact.email})")
    if contact.phone:
        contact_parts.append(f"📱 {contact.phone}")
    if contact.location:
        contact_parts.append(f"📍 {contact.location}")
    if contact.linkedin:
        contact_parts.append(f"🔗 [LinkedIn]({contact.linkedin})")
    if contact.github:
        contact_parts.append(f"💻 [GitHub]({contact.github})")
        
    contact_line = " | ".join(contact_parts)
    
    # Generar la sección de habilidades
    skills_line = ", ".join(cv.optimized_skills)

    # Construir el currículum en Markdown
    md = []
    md.append(f"# {cv.full_name}")
    md.append(f"{contact_line}\n")
    md.append("---")
    md.append(f"## {headers['summary']}")
    md.append(cv.professional_summary)
    md.append("\n---")
    md.append(f"## {headers['skills']}")
    md.append(f"**{headers['skills_label']}:** {skills_line}")
    md.append("\n---")
    md.append(f"## {headers['experience']}")
    
    for exp in cv.experiences:
        md.append(f"### {exp.role}")
        md.append(f"**{exp.company}** | *{exp.period}*\n")
        for ach in exp.tailored_achievements:
            md.append(f"- {ach}")
        md.append("") # Línea en blanco para separar
        
    md.append("---")
    md.append(f"## {headers['education']}")
    
    for edu in cv.education:
        md.append(f"### {edu.degree}")
        md.append(f"**{edu.institution}** | *{edu.period}*\n")
        for ach in edu.achievements:
            md.append(f"- {ach}")
        md.append("") # Línea en blanco para separar

    md.append(f"\n*{headers['footer']}*")
    
    return "\n".join(md)

def generate_html(cv: OptimizedCV, template_path: str = "templates/cv_template.html", lang: str = "es") -> str:
    """
    Convierte el modelo de datos de OptimizedCV en un documento HTML interactivo con estilos premium y listos para PDF,
    utilizando una plantilla externa Jinja2.
    
    Args:
        cv (OptimizedCV): El CV optimizado devuelto por Gemini.
        template_path (str): Ruta al archivo de plantilla HTML Jinja2.
        lang (str): Idioma de salida ('es' o 'en').
        
    Returns:
        str: El contenido del documento HTML con diseño responsivo y optimizado para impresión.
    """
    # Intentar resolver la ruta relativa al archivo actual si no existe en la ruta de trabajo actual
    if not os.path.exists(template_path):
        fallback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), template_path)
        if os.path.exists(fallback_path):
            template_path = fallback_path

    if not os.path.exists(template_path):
        print(f"\n[ERROR] No se pudo encontrar la plantilla HTML en la ruta: '{template_path}'")
        sys.exit(1)

    try:
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()
        
        template = jinja2.Template(template_content)
        headers = HEADERS.get(lang, HEADERS["es"])
        
        rendered_html = template.render(
            cv=cv,
            lang=lang,
            headers=headers
        )
        return rendered_html
    except Exception as exc:
        print(f"\n[ERROR] Error al cargar o renderizar la plantilla HTML en '{template_path}':")
        print(exc)
        sys.exit(1)
