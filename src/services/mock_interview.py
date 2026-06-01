"""
MockInterviewService — Servicio de entrevista técnica simulada con IA.

Utiliza el chat multi-turno de la SDK google-genai para simular una entrevista
técnica interactiva basada en las tecnologías del CV del candidato y la
descripción del puesto de trabajo (JD). Mantiene historial de mensajes
(Chat Memory) con system_instruction.

Flujo:
  1. Carga el perfil YAML y la JD.
  2. Construye un system_instruction que restringe al entrevistador a SOLO
     preguntar sobre tecnologías presentes en el CV y la JD.
  3. Ejecuta un loop interactivo de máximo 7 preguntas.
  4. Tras la última respuesta, solicita feedback estructurado al modelo.
  5. Exporta la transcripción completa a output/interview_transcript.md.
"""

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
from google.genai import types

# Cargar variables de entorno
load_dotenv()

# ─── Constantes ───────────────────────────────────────────────────────────────
MAX_QUESTIONS = 7
DEFAULT_PROFILE_PATH = "config/student_profile.yaml"
DEFAULT_JD_PATH = "job_description.txt"
DEFAULT_OUTPUT_PATH = "output/interview_transcript.md"
MODEL_NAME = "gemini-2.5-flash"


def _build_system_instruction(profile: dict, job_description: str) -> str:
    """
    Construye el system_instruction que define el comportamiento del
    entrevistador IA, restringiéndolo a las tecnologías del CV y la JD.
    """
    profile_yaml = yaml.dump(profile, allow_unicode=True, default_flow_style=False)

    return (
        "Eres un entrevistador técnico senior experimentado y empático, realizando una "
        "entrevista técnica para un puesto junior/trainee.\n\n"
        "─── REGLAS ESTRICTAS ───\n"
        "1. SOLO puedes hacer preguntas sobre tecnologías, herramientas y conceptos que "
        "aparezcan EXPLÍCITAMENTE en el perfil del candidato (CV) o en la descripción del "
        "puesto (JD) que se proporcionan a continuación. NO preguntes sobre tecnologías "
        "que no estén listadas en ninguno de estos dos documentos.\n"
        "2. Las preguntas deben ser de nivel junior/trainee: prácticas, claras y directas. "
        "Evita preguntas excesivamente abstractas o de nivel senior.\n"
        "3. Haz UNA sola pregunta por turno. No hagas múltiples preguntas en un mismo mensaje.\n"
        "4. Después de que el candidato responda, haz un breve comentario (1-2 oraciones) "
        "reconociendo su respuesta antes de pasar a la siguiente pregunta.\n"
        "5. Varía los temas: cubre diferentes tecnologías y conceptos del CV y la JD, "
        "no repitas temas ya preguntados.\n"
        "6. Mantén un tono profesional pero amigable y motivador.\n"
        "7. Responde SIEMPRE en español.\n\n"
        "─── PERFIL DEL CANDIDATO (CV) ───\n"
        f"{profile_yaml}\n\n"
        "─── DESCRIPCIÓN DEL PUESTO (JD) ───\n"
        f"{job_description}\n"
    )


def _build_feedback_prompt() -> str:
    """
    Construye el prompt que solicita el feedback final estructurado al modelo.
    """
    return (
        "La entrevista ha terminado. Ahora, proporciona un feedback estructurado y "
        "constructivo al candidato basándote EXCLUSIVAMENTE en sus respuestas durante "
        "esta entrevista. Usa el siguiente formato:\n\n"
        "## 🎯 Resumen General\n"
        "Un párrafo con la impresión general del desempeño del candidato.\n\n"
        "## ✅ Fortalezas Demostradas\n"
        "Lista con viñetas de los puntos fuertes observados en sus respuestas.\n\n"
        "## 🔧 Áreas de Mejora\n"
        "Lista con viñetas de los aspectos que el candidato debería reforzar, "
        "con sugerencias concretas de estudio o práctica.\n\n"
        "## 📚 Recursos Recomendados\n"
        "Lista de 3-5 recursos específicos (libros, cursos, documentación oficial, "
        "proyectos prácticos) para que el candidato mejore en las áreas detectadas.\n\n"
        "## 💯 Puntuación Estimada\n"
        "Una puntuación del 1 al 10 con una breve justificación.\n\n"
        "Sé honesto pero motivador. Recuerda que el candidato es junior/trainee."
    )


class MockInterviewService:
    """
    Servicio de entrevista técnica simulada que utiliza Gemini como
    entrevistador IA con Chat Memory (historial multi-turno).

    Attributes:
        profile: Datos del perfil del candidato (dict del YAML).
        job_description: Texto de la descripción del puesto.
        transcript: Lista de tuplas (rol, mensaje) con la conversación.
        question_count: Contador de preguntas realizadas por el entrevistador.
        output_path: Ruta donde se exportará la transcripción.
    """

    def __init__(
        self,
        profile_path: str = DEFAULT_PROFILE_PATH,
        jd_path: str = DEFAULT_JD_PATH,
        output_path: str = DEFAULT_OUTPUT_PATH,
    ):
        # Validar API Key
        self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
            print("Configúrala en el archivo .env o exportándola en la terminal.")
            sys.exit(1)

        # Cargar perfil y JD
        self.profile = self._load_yaml(profile_path)
        self.job_description = self._load_text(jd_path)
        self.output_path = output_path

        # Estado de la entrevista
        self.transcript: list[tuple[str, str]] = []
        self.question_count: int = 0
        self._chat_session = None
        self._client = None

    # ─── Métodos privados de carga ────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: str) -> dict:
        """Carga y valida un archivo YAML."""
        if not os.path.exists(path):
            print(f"\n[ERROR] No se encontró el archivo de perfil: '{path}'")
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

    # ─── Inicialización del chat ──────────────────────────────────────────────

    def _init_chat(self) -> None:
        """
        Inicializa el cliente de Gemini y crea una sesión de chat multi-turno
        con system_instruction que restringe al entrevistador.
        """
        try:
            self._client = genai.Client()
        except Exception as exc:
            print(f"\n[ERROR] Falló la inicialización del cliente GenAI: {exc}")
            sys.exit(1)

        system_instruction = _build_system_instruction(self.profile, self.job_description)

        # Crear chat multi-turno con system_instruction (Chat Memory)
        self._chat_session = self._client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )

    def _send_message(self, message: str) -> str:
        """
        Envía un mensaje al chat y retorna la respuesta del modelo.
        El historial se mantiene automáticamente (Chat Memory).
        """
        response = self._chat_session.send_message(message)
        return response.text

    # ─── Método principal: run_interactive ────────────────────────────────────

    def run_interactive(self) -> None:
        """
        Ejecuta la entrevista técnica interactiva en la terminal.

        Flujo:
          1. Inicializa el chat con Gemini.
          2. Solicita la primera pregunta al entrevistador IA.
          3. Loop interactivo: el candidato responde → el entrevistador hace
             la siguiente pregunta. Máximo MAX_QUESTIONS preguntas.
          4. Tras la última respuesta, solicita feedback estructurado.
          5. Exporta la transcripción automáticamente.
        """
        print("=" * 64)
        print("   🎤 ENTREVISTA TÉCNICA SIMULADA — Jr Career Copilot")
        print("=" * 64)
        print(f"\n📋 Perfil cargado: {self.profile.get('personal_info', {}).get('full_name', 'Candidato')}")
        print(f"💼 Puesto objetivo: {self.job_description.splitlines()[0]}")
        print(f"❓ Máximo de preguntas: {MAX_QUESTIONS}")
        print("\n💡 Escribe 'salir' en cualquier momento para terminar la entrevista.\n")
        print("-" * 64)

        # Inicializar chat con Gemini
        print("\n⏳ Conectando con el entrevistador IA...\n")
        self._init_chat()

        # Solicitar la primera pregunta
        opening = (
            "Comienza la entrevista técnica. Preséntate brevemente como entrevistador "
            "y haz tu primera pregunta técnica al candidato. Recuerda: solo sobre "
            "tecnologías del CV y la JD."
        )
        first_question = self._send_message(opening)
        self.transcript.append(("Entrevistador", first_question))
        self.question_count = 1
        print(f"🤖 Entrevistador:\n{first_question}\n")

        # Loop interactivo
        while self.question_count < MAX_QUESTIONS:
            # Leer respuesta del candidato
            try:
                user_input = input("👤 Tú: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n⚠️  Entrevista interrumpida por el usuario.")
                break

            if not user_input:
                print("⚠️  Por favor escribe una respuesta.\n")
                continue

            if user_input.lower() == "salir":
                print("\n⚠️  Saliendo de la entrevista anticipadamente...")
                self.transcript.append(("Candidato", "[Salió de la entrevista]"))
                break

            # Registrar respuesta del candidato
            self.transcript.append(("Candidato", user_input))

            # Obtener siguiente pregunta del entrevistador
            next_turn_prompt = (
                f"El candidato respondió. Esta es la pregunta #{self.question_count} de {MAX_QUESTIONS}. "
                f"Haz un breve comentario sobre su respuesta y luego formula la siguiente "
                f"pregunta técnica sobre un tema diferente del CV o la JD."
            )
            context_message = f"{user_input}\n\n[Instrucción interna: {next_turn_prompt}]"

            response = self._send_message(context_message)
            self.question_count += 1
            self.transcript.append(("Entrevistador", response))
            print(f"\n🤖 Entrevistador:\n{response}\n")

        # ─── Última respuesta del candidato (si aplica) ──────────────────────
        if self.question_count >= MAX_QUESTIONS:
            print(f"\n📝 Última pregunta ({MAX_QUESTIONS}/{MAX_QUESTIONS}). Responde para recibir tu feedback.\n")
            try:
                last_answer = input("👤 Tú: ").strip()
                if last_answer and last_answer.lower() != "salir":
                    self.transcript.append(("Candidato", last_answer))
                    # Enviar la última respuesta al modelo para que la considere en el feedback
                    self._send_message(last_answer)
            except (EOFError, KeyboardInterrupt):
                pass

        # ─── Feedback final ──────────────────────────────────────────────────
        print("\n" + "=" * 64)
        print("   📊 GENERANDO FEEDBACK DE LA ENTREVISTA...")
        print("=" * 64 + "\n")

        feedback_prompt = _build_feedback_prompt()
        feedback = self._send_message(feedback_prompt)
        self.transcript.append(("Feedback", feedback))
        print(feedback)

        # ─── Exportar transcripción ──────────────────────────────────────────
        self.export_transcript()

    # ─── Método: export_transcript ────────────────────────────────────────────

    def export_transcript(self, output_path: Optional[str] = None) -> str:
        """
        Exporta la transcripción completa de la entrevista a un archivo Markdown.

        Args:
            output_path: Ruta de salida (opcional, usa self.output_path por defecto).

        Returns:
            str: La ruta absoluta del archivo generado.
        """
        path = output_path or self.output_path

        # Crear directorio si no existe
        output_dir = os.path.dirname(path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Construir contenido Markdown
        candidate_name = self.profile.get("personal_info", {}).get("full_name", "Candidato")
        jd_title = self.job_description.splitlines()[0] if self.job_description else "N/A"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            f"# 🎤 Transcripción de Entrevista Técnica Simulada",
            "",
            f"**Candidato:** {candidate_name}  ",
            f"**Puesto:** {jd_title}  ",
            f"**Fecha:** {timestamp}  ",
            f"**Preguntas realizadas:** {self.question_count} / {MAX_QUESTIONS}",
            "",
            "---",
            "",
        ]

        for role, message in self.transcript:
            if role == "Feedback":
                lines.append("---")
                lines.append("")
                lines.append("## 📊 Feedback del Entrevistador")
                lines.append("")
                lines.append(message)
            elif role == "Entrevistador":
                lines.append(f"### 🤖 Entrevistador")
                lines.append("")
                lines.append(message)
                lines.append("")
            else:  # Candidato
                lines.append(f"### 👤 Candidato")
                lines.append("")
                lines.append(message)
                lines.append("")

        content = "\n".join(lines)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        abs_path = os.path.abspath(path)
        print(f"\n✅ Transcripción exportada en: '{abs_path}'")
        return abs_path


# ─── Punto de entrada directo ─────────────────────────────────────────────────

def main():
    """Punto de entrada para ejecutar la entrevista desde la línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Entrevista técnica simulada con IA para ingenieros junior."
    )
    parser.add_argument(
        "-p", "--profile",
        default=DEFAULT_PROFILE_PATH,
        help=f"Ruta al perfil YAML del candidato (por defecto: {DEFAULT_PROFILE_PATH})."
    )
    parser.add_argument(
        "-j", "--job",
        default=DEFAULT_JD_PATH,
        help=f"Ruta a la descripción del puesto (por defecto: {DEFAULT_JD_PATH})."
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Ruta de salida para la transcripción (por defecto: {DEFAULT_OUTPUT_PATH})."
    )
    args = parser.parse_args()

    service = MockInterviewService(
        profile_path=args.profile,
        jd_path=args.job,
        output_path=args.output,
    )
    service.run_interactive()


if __name__ == "__main__":
    main()
