"""
RobustnessJudgeService — Validador de robustez del CV optimizado por IA.

Utiliza Gemini con Structured Outputs (response_mime_type="application/json"
+ response_schema) para analizar el CV optimizado y detectar:
  1. Alucinaciones: datos fabricados o exagerados que no existen en el perfil original.
  2. Inconsistencias: errores lógicos, fechas que no cuadran, contradicciones.
  3. Compliance ético: verificación de que no se fabrican títulos, métricas ni certificaciones.

Exporta un reporte JSON válido y estructurado a output/robustness_report.json.
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

import yaml
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

from models import ReporteRobustez

# Cargar variables de entorno
load_dotenv()

# ─── Constantes ───────────────────────────────────────────────────────────────
DEFAULT_PROFILE_PATH = "config/student_profile.yaml"
DEFAULT_JD_PATH = "job_description.txt"
DEFAULT_CV_PATH = "output/optimized_cv.md"
DEFAULT_OUTPUT_PATH = "output/robustness_report.json"
MODEL_NAME = "gemini-2.5-flash"


def _build_validation_prompt(
    profile_yaml: str,
    job_description: str,
    optimized_cv: str,
) -> str:
    """
    Construye el prompt que instruye al modelo a actuar como juez de robustez,
    comparando el CV optimizado contra el perfil original y la JD.
    """
    return (
        "Eres un auditor de calidad experto en currículums generados por IA. "
        "Tu trabajo es comparar un CV optimizado por IA contra el perfil ORIGINAL "
        "del candidato y la descripción del puesto, para detectar problemas de "
        "veracidad y calidad.\n\n"
        "Realiza las siguientes validaciones exhaustivas:\n\n"
        "─── 1. DETECCIÓN DE ALUCINACIONES ───\n"
        "Compara CADA dato del CV optimizado contra el perfil original del candidato.\n"
        "Busca:\n"
        "  - 'fabricacion': Habilidades, certificaciones, empresas, logros o tecnologías "
        "que NO aparecen en el perfil original y fueron inventadas.\n"
        "  - 'exageracion': Datos reales que fueron inflados (ej: 'lideró un equipo de 10' "
        "cuando el perfil dice 'colaboró en un equipo', o métricas numéricas inventadas "
        "como '40% de mejora' sin datos originales que las sustenten).\n"
        "  - 'atribucion_falsa': Logros o responsabilidades atribuidas al candidato que "
        "corresponden a otros roles o que no están en su perfil.\n\n"
        "─── 2. DETECCIÓN DE INCONSISTENCIAS ───\n"
        "Busca errores lógicos o factuales:\n"
        "  - Fechas que no cuadran o se solapan de forma imposible.\n"
        "  - Roles o títulos que contradicen el perfil original.\n"
        "  - Tecnologías mencionadas en logros pero no en la lista de skills.\n"
        "  - Información de contacto modificada o alterada.\n"
        "  - Períodos de estudio o trabajo que no coinciden con el original.\n\n"
        "─── 3. VALIDACIÓN DE COMPLIANCE ÉTICO ───\n"
        "Evalúa los siguientes criterios éticos (responde si cumple o no para cada uno):\n"
        "  - 'No fabricación de títulos académicos': No se inventaron grados, títulos ni instituciones.\n"
        "  - 'No fabricación de certificaciones': No se añadieron certificaciones inexistentes.\n"
        "  - 'No inflación de métricas cuantitativas': No se inventaron porcentajes, números "
        "o métricas sin base en el perfil original.\n"
        "  - 'Preservación de identidad': Nombre, contacto y datos personales se mantienen fieles.\n"
        "  - 'No fabricación de experiencia laboral': No se inventaron empresas ni roles.\n"
        "  - 'Veracidad de tecnologías': Solo se mencionan tecnologías presentes en el perfil original.\n"
        "  - 'Lenguaje apropiado': El tono es profesional, no engañoso ni manipulador.\n\n"
        "─── DOCUMENTOS DE REFERENCIA ───\n\n"
        "## PERFIL ORIGINAL DEL CANDIDATO (FUENTE DE VERDAD):\n"
        f"```yaml\n{profile_yaml}\n```\n\n"
        "## DESCRIPCIÓN DEL PUESTO DE TRABAJO:\n"
        f"```\n{job_description}\n```\n\n"
        "## CV OPTIMIZADO POR IA (DOCUMENTO A EVALUAR):\n"
        f"```markdown\n{optimized_cv}\n```\n\n"
        "─── INSTRUCCIONES FINALES ───\n"
        "- Sé EXTREMADAMENTE riguroso y específico en cada hallazgo.\n"
        "- Si NO encuentras alucinaciones ni inconsistencias, devuelve listas vacías y una "
        "puntuación alta.\n"
        "- La puntuación general debe reflejar la gravedad de los problemas encontrados.\n"
        "- Responde SIEMPRE en español.\n"
    )


class RobustnessJudgeService:
    """
    Servicio de validación de robustez que actúa como 'juez' del CV optimizado.

    Compara el CV generado por IA contra el perfil original del candidato y la JD,
    usando Gemini con Structured Outputs para garantizar un reporte JSON válido.

    Attributes:
        profile: Datos originales del candidato (dict del YAML).
        job_description: Texto de la descripción del puesto.
        optimized_cv: Contenido del CV optimizado (Markdown).
        output_path: Ruta donde se exportará el reporte JSON.
        report: Reporte de robustez generado (None hasta que se ejecute run_validation).
    """

    def __init__(
        self,
        profile_path: str = DEFAULT_PROFILE_PATH,
        jd_path: str = DEFAULT_JD_PATH,
        cv_path: str = DEFAULT_CV_PATH,
        output_path: str = DEFAULT_OUTPUT_PATH,
    ):
        # Validar API Key
        self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
            print("Configúrala en el archivo .env o exportándola en la terminal.")
            sys.exit(1)

        # Cargar los tres documentos de entrada
        self.profile = self._load_yaml(profile_path)
        self.job_description = self._load_text(jd_path)
        self.optimized_cv = self._load_text(cv_path)
        self.output_path = output_path

        # Estado
        self.report: Optional[ReporteRobustez] = None

    # ─── Métodos privados de carga ────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: str) -> dict:
        """Carga y valida un archivo YAML."""
        if not os.path.exists(path):
            print(f"\n[ERROR] No se encontró el archivo: '{path}'")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                print(f"\n[ERROR] El archivo '{path}' está vacío.")
                sys.exit(1)
            return data

    @staticmethod
    def _load_text(path: str) -> str:
        """Carga un archivo de texto plano."""
        if not os.path.exists(path):
            print(f"\n[ERROR] No se encontró el archivo: '{path}'")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"\n[ERROR] El archivo '{path}' está vacío.")
                sys.exit(1)
            return content

    # ─── Método principal: run_validation ─────────────────────────────────────

    def run_validation(self) -> ReporteRobustez:
        """
        Ejecuta la validación de robustez del CV optimizado.

        Envía el perfil original, la JD y el CV optimizado a Gemini con
        Structured Outputs (response_mime_type="application/json" + response_schema)
        para obtener un reporte JSON válido y tipado.

        Returns:
            ReporteRobustez: Objeto Pydantic con el reporte completo de validación.
        """
        print("=" * 64)
        print("   ⚖️  ROBUSTNESS JUDGE — Validación de CV Optimizado")
        print("=" * 64)

        candidate_name = self.profile.get("personal_info", {}).get("full_name", "Candidato")
        print(f"\n📋 Candidato: {candidate_name}")
        print(f"📄 CV optimizado: {DEFAULT_CV_PATH}")
        print(f"🔍 Validando: alucinaciones, inconsistencias, compliance ético...\n")

        # Inicializar cliente de Gemini
        try:
            client = genai.Client()
        except Exception as exc:
            print(f"\n[ERROR] Falló la inicialización del cliente GenAI: {exc}")
            sys.exit(1)

        # Construir prompt
        profile_yaml = yaml.dump(self.profile, allow_unicode=True, default_flow_style=False)
        prompt = _build_validation_prompt(profile_yaml, self.job_description, self.optimized_cv)

        print("[INFO] Enviando documentos a Gemini para análisis de robustez...")

        try:
            # Llamada con Structured Outputs
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReporteRobustez,
                temperature=0.1,  # Máxima consistencia para validación
                system_instruction=(
                    "Eres un auditor de calidad de IA especializado en detectar alucinaciones, "
                    "inconsistencias y violaciones éticas en currículums generados por inteligencia artificial. "
                    "Tu análisis debe ser exhaustivo, preciso y constructivo. "
                    "Responde siempre en español."
                ),
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise ValueError("Gemini devolvió una respuesta vacía.")

            # Validar con Pydantic
            self.report = ReporteRobustez.model_validate_json(response.text)
            print("[INFO] Análisis de robustez completado con éxito.\n")

        except Exception as exc:
            print(f"\n[ERROR] Falló la validación con Gemini: {exc}")
            print("Verifica tu conexión a internet y tu API Key.")
            sys.exit(1)

        # Mostrar resumen en consola
        self._print_summary()

        # Exportar reporte
        self._export_report()

        return self.report

    # ─── Visualización en consola ─────────────────────────────────────────────

    def _print_summary(self) -> None:
        """Imprime un resumen visual del reporte en la consola."""
        if not self.report:
            return

        r = self.report

        # Icono de veredicto
        verdict_icon = {
            "APROBADO": "✅",
            "APROBADO_CON_OBSERVACIONES": "⚠️",
            "RECHAZADO": "❌",
        }.get(r.veredicto, "❓")

        print("-" * 64)
        print(f"  {verdict_icon} VEREDICTO: {r.veredicto}")
        print(f"  📊 Puntuación: {r.puntuacion_general}/10.0")
        print("-" * 64)
        print(f"\n📝 {r.resumen_ejecutivo}\n")

        # Alucinaciones
        print(f"🔴 Alucinaciones detectadas: {r.total_alucinaciones}")
        if r.alucinaciones:
            for i, a in enumerate(r.alucinaciones, 1):
                print(f"   {i}. [{a.severidad.upper()}] [{a.tipo}] Campo: {a.campo}")
                print(f"      Generado: {a.valor_generado[:100]}...")
                if a.valor_original:
                    print(f"      Original: {a.valor_original[:100]}...")
                print(f"      Motivo: {a.explicacion[:120]}...")
                print()

        # Inconsistencias
        print(f"🟡 Inconsistencias detectadas: {r.total_inconsistencias}")
        if r.inconsistencias:
            for i, inc in enumerate(r.inconsistencias, 1):
                print(f"   {i}. [{inc.severidad.upper()}] {inc.campo_afectado}: {inc.descripcion[:120]}")
            print()

        # Compliance ético
        etica_ok = sum(1 for v in r.validacion_etica if v.cumple)
        etica_total = len(r.validacion_etica)
        print(f"🟢 Compliance ético: {etica_ok}/{etica_total} criterios aprobados")
        for v in r.validacion_etica:
            icon = "✅" if v.cumple else "❌"
            print(f"   {icon} {v.criterio}: {v.detalle[:100]}")
        print()

        # Recomendaciones
        if r.recomendaciones:
            print("💡 Recomendaciones:")
            for i, rec in enumerate(r.recomendaciones, 1):
                print(f"   {i}. {rec}")
            print()

    # ─── Exportación del reporte ──────────────────────────────────────────────

    def _export_report(self, output_path: Optional[str] = None) -> str:
        """
        Exporta el reporte de robustez a un archivo JSON válido.

        Args:
            output_path: Ruta de salida (opcional, usa self.output_path por defecto).

        Returns:
            str: Ruta absoluta del archivo generado.
        """
        if not self.report:
            print("[WARN] No hay reporte para exportar. Ejecuta run_validation() primero.")
            return ""

        path = output_path or self.output_path

        # Crear directorio si no existe
        output_dir = os.path.dirname(path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Construir JSON con metadatos adicionales
        report_data = {
            "metadata": {
                "generado_en": datetime.now().isoformat(),
                "modelo_evaluador": MODEL_NAME,
                "candidato": self.profile.get("personal_info", {}).get("full_name", "N/A"),
                "cv_evaluado": DEFAULT_CV_PATH,
            },
            "reporte": self.report.model_dump(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        abs_path = os.path.abspath(path)
        print(f"✅ Reporte de robustez exportado en: '{abs_path}'")
        return abs_path


# ─── Punto de entrada directo ─────────────────────────────────────────────────

def main():
    """Punto de entrada para ejecutar la validación desde la línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Robustness Judge — Validador de CV optimizado por IA."
    )
    parser.add_argument(
        "-p", "--profile",
        default=DEFAULT_PROFILE_PATH,
        help=f"Ruta al perfil YAML original (por defecto: {DEFAULT_PROFILE_PATH})."
    )
    parser.add_argument(
        "-j", "--job",
        default=DEFAULT_JD_PATH,
        help=f"Ruta a la descripción del puesto (por defecto: {DEFAULT_JD_PATH})."
    )
    parser.add_argument(
        "-c", "--cv",
        default=DEFAULT_CV_PATH,
        help=f"Ruta al CV optimizado a evaluar (por defecto: {DEFAULT_CV_PATH})."
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Ruta de salida para el reporte JSON (por defecto: {DEFAULT_OUTPUT_PATH})."
    )
    args = parser.parse_args()

    service = RobustnessJudgeService(
        profile_path=args.profile,
        jd_path=args.job,
        cv_path=args.cv,
        output_path=args.output,
    )
    service.run_validation()


if __name__ == "__main__":
    main()
