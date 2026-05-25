import os
import sys
import argparse
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Reconfigurar salida estándar para soportar UTF-8 (evita errores con emojis en Windows)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Cargar variables de entorno desde el archivo .env si existe
load_dotenv()

# Re-exportar de forma transparente clases, funciones y variables para asegurar 100% de retrocompatibilidad
from models import (
    ContactInfo,
    OptimizedExperience,
    OptimizedEducation,
    OptimizedCV
)
from file_io import (
    load_profile,
    load_job_description,
    save_markdown,
    save_html
)
from renderers import (
    HEADERS,
    generate_markdown,
    generate_html
)
from optimizer import optimize_cv
from services.mock_interview import MockInterviewService
from services.robustness_judge import RobustnessJudgeService

def parse_arguments() -> argparse.Namespace:
    """
    Analiza los argumentos de la línea de comandos.
    
    Returns:
        argparse.Namespace: Los argumentos analizados por el parser.
    """
    parser = argparse.ArgumentParser(
        description="Optimizador de CV con Inteligencia Artificial para Ingenieros Junior."
    )
    parser.add_argument(
        "-j", "--job",
        required=True,
        help="Ruta al archivo de texto plano (.txt) que contiene la descripción del trabajo/vacante."
    )
    parser.add_argument(
        "-p", "--profile",
        default="config/student_profile.yaml",
        help="Ruta al archivo de perfil YAML del ingeniero junior (por defecto: config/student_profile.yaml)."
    )
    parser.add_argument(
        "-o", "--output",
        default="output/optimized_cv.md",
        help="Ruta donde se guardará el currículum optimizado en formato Markdown (por defecto: output/optimized_cv.md)."
    )
    parser.add_argument(
        "-l", "--lang",
        default="es",
        choices=["es", "en"],
        help="Idioma de salida del currículum optimizado: 'es' (español) o 'en' (inglés) (por defecto: 'es')."
    )
    parser.add_argument(
        "-t", "--template",
        default="templates/cv_template.html",
        help="Ruta a la plantilla HTML Jinja2 (por defecto: templates/cv_template.html)."
    )
    parser.add_argument(
        "--mock-interview",
        action="store_true",
        default=False,
        help="Lanza una entrevista técnica simulada con IA en lugar de optimizar el CV."
    )
    parser.add_argument(
        "--robustness",
        action="store_true",
        default=False,
        help="Ejecuta el Robustness Judge para validar alucinaciones, inconsistencias y compliance ético del CV optimizado."
    )
    return parser.parse_args()

def main() -> None:
    """
    Función de ejecución principal del optimizador.
    """
    print("=" * 60)
    print("      OPTIMIZADOR DE CV PARA INGENIEROS JUNIOR / TRAINEES   ")
    print("=" * 60)
    
    # 1. Analizar argumentos de consola
    args = parse_arguments()
    
    # ── Modo: Entrevista técnica simulada ─────────────────────────────
    if args.mock_interview:
        service = MockInterviewService(
            profile_path=args.profile,
            jd_path=args.job,
            output_path="output/interview_transcript.md",
        )
        service.run_interactive()
        return
    
    # ── Modo: Robustness Check (standalone) ───────────────────────────
    if args.robustness:
        judge = RobustnessJudgeService(
            profile_path=args.profile,
            jd_path=args.job,
            cv_path=args.output,
            output_path="output/robustness_report.json",
        )
        judge.run_validation()
        return
    
    # ── Modo: Optimización de CV (flujo por defecto) ─────────────────
    # 2. Cargar perfil de ingeniero junior
    print(f"[INFO] Cargando perfil del ingeniero junior desde: '{args.profile}'...")
    profile = load_profile(args.profile)
    
    # 3. Cargar descripción del trabajo
    print(f"[INFO] Cargando descripción de la oferta laboral en: '{args.job}'...")
    job_description = load_job_description(args.job)
    
    # 4. Optimizar el CV mediante la API de Gemini
    optimized_cv = optimize_cv(profile, job_description, args.lang)
    
    # 5. Generar formato Markdown
    print("[INFO] Generando representación en formato Markdown...")
    markdown_content = generate_markdown(optimized_cv, args.lang)
    
    # 6. Generar formato HTML
    print("[INFO] Generando representación en formato HTML premium...")
    html_content = generate_html(optimized_cv, args.template, args.lang)
    
    # 7. Guardar archivos finales
    save_markdown(markdown_content, args.output)
    
    # Derivar la ruta del archivo HTML reemplazando la extensión .md del output
    html_output_path = os.path.splitext(args.output)[0] + ".html"
    save_html(html_content, html_output_path)
    
    print("=" * 60)
    print("¡Proceso finalizado con éxito! Éxito en tu postulación laboral.")
    print("=" * 60)

if __name__ == "__main__":
    main()
