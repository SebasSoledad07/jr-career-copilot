"""
PromptOptimizerService — Servicio para optimizar el prompt del CV en base a reportes de alucinaciones.

Utiliza Gemini 2.5 Flash para recibir la plantilla base del prompt, el reporte de alucinaciones
y las recomendaciones de corrección, y re-escribir/mejorar el prompt inyectando instrucciones
negativas y reglas específicas que prevengan que vuelvan a ocurrir las mismas alucinaciones.
"""

import os
import sys
import json
from datetime import datetime
from google import genai
from google.genai import types

from optimizer import DEFAULT_PROMPT_TEMPLATE, parse_custom_prompt

# Reconfigurar salida estándar para UTF-8 en Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class PromptOptimizerService:
    """
    Servicio de optimización del prompt que refina las instrucciones para Gemini.
    """

    def __init__(
        self,
        report_path: str = "output/robustness_report.json",
        output_path: str = "output/improved_prompt.md",
    ):
        # Validar API Key
        self._api_key = os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
            print("Configúrala en el archivo .env o exportándola en la terminal.")
            sys.exit(1)

        self.report_path = report_path
        self.output_path = output_path

    def run_optimization(self) -> str:
        """
        Ejecuta la optimización del prompt llamando a Gemini.
        Carga el reporte, construye el meta-prompt, genera el nuevo prompt y lo escribe en el .md de salida.
        
        Returns:
            str: El contenido completo del archivo Markdown generado.
        """
        print("=" * 64)
        print("   🧠 PROMPT OPTIMIZER — Mejora del Prompt mediante Alucinaciones")
        print("=" * 64)

        if not os.path.exists(self.report_path):
            print(f"\n[ERROR] No se pudo encontrar el reporte de robustez en: '{self.report_path}'")
            print("Sugerencia: Primero ejecuta el Robustness Judge con `python src/cv_optimizer.py -j <job> --robustness`.")
            sys.exit(1)

        print(f"\n[INFO] Cargando reporte de robustez desde '{self.report_path}'...")
        with open(self.report_path, "r", encoding="utf-8") as f:
            try:
                report_data = json.load(f)
            except Exception as e:
                print(f"[ERROR] No se pudo analizar el reporte de robustez JSON: {e}")
                sys.exit(1)

        reporte = report_data.get("reporte", {})
        alucinaciones = reporte.get("alucinaciones", [])
        inconsistencias = reporte.get("inconsistencias", [])
        recomendaciones = reporte.get("recomendaciones", [])
        puntuacion_general = reporte.get("puntuacion_general", "N/A")
        veredicto = reporte.get("veredicto", "N/A")

        if not alucinaciones and not inconsistencias:
            print("[INFO] El reporte no registra alucinaciones ni inconsistencias.")
            print("[INFO] Generando versión estándar del prompt personalizado para revisión manual.")

        # Construir meta-prompt para Gemini
        meta_prompt = (
            "You are a master AI prompt engineer and LLM instructor.\n"
            "Your task is to refine and optimize an existing CV optimization prompt template to prevent specific "
            "hallucinations and errors previously made by the model.\n\n"
            "Here is the BASE PROMPT TEMPLATE used for CV optimization:\n"
            "```prompt\n"
            f"{DEFAULT_PROMPT_TEMPLATE}\n"
            "```\n\n"
            "Here are the errors and hallucinations detected during a robustness audit:\n"
        )

        if alucinaciones:
            meta_prompt += "### DETECTED HALLUCINATIONS:\n"
            for a in alucinaciones:
                meta_prompt += (
                    f"- Campo: `{a.get('campo')}`\n"
                    f"  Tipo: {a.get('tipo')} (Severidad: {a.get('severidad')})\n"
                    f"  Valor Generado: \"{a.get('valor_generado')}\"\n"
                    f"  Valor Original: \"{a.get('valor_original')}\"\n"
                    f"  Explicación: {a.get('explicacion')}\n\n"
                )

        if inconsistencias:
            meta_prompt += "### DETECTED INCONSISTENCIES:\n"
            for inc in inconsistencias:
                meta_prompt += f"- Campo afectado: `{inc.get('campo_afectado')}`\n  Descripción: {inc.get('descripcion')}\n\n"

        if recomendaciones:
            meta_prompt += "### RECOMMENDATIONS FOR FIXING:\n"
            for rec in recomendaciones:
                meta_prompt += f"- {rec}\n"

        meta_prompt += (
            "\nINSTRUCTIONS FOR REWRITING THE PROMPT:\n"
            "1. You must keep the core goals, Pygmalion Effect instructions, and critical language rules of the base prompt.\n"
            "2. Add a dedicated section (e.g. '--- ANTI-HALLUCINATION & TRUTHFULNESS CONSTRAINTS ---') to the prompt template.\n"
            "3. Inside this section, write explicit negative constraints and correction rules directly addressing the "
            "detected hallucinations. For example, instruct the model never to use terms like 'Lideré' or other active leadership verbs "
            "for academic/personal projects if the profile only says 'diseño y desarrollo' (design and development).\n"
            "4. IMPORTANT: Keep all existing placeholder variables `{profile_yaml}`, `{job_description}`, `{language_name}`, and `{lang}` intact and unused inside the template. The script will replace them at runtime. Do NOT replace them with real data now.\n"
            "5. Make sure the output format of the prompt you write is robust, clear, and easy to parse.\n"
            "6. Return ONLY the refined/improved prompt template. Do not include any introductory or concluding remarks outside the template, just the final prompt template."
        )

        print("[INFO] Conectando con Gemini para refinar el prompt...")
        try:
            client = genai.Client()
            config = types.GenerateContentConfig(
                temperature=0.2,
                system_instruction=(
                    "You are an expert AI prompt engineer. You refine templates to introduce guardrails, "
                    "negative constraints, and formatting rules that prevent LLMs from hallucinating or exaggerating. "
                    "You return the updated prompt template exactly as requested, keeping placeholders intact."
                )
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=meta_prompt,
                config=config
            )
        except Exception as exc:
            print(f"\n[ERROR] Falló la llamada a la API de Gemini: {exc}")
            sys.exit(1)

        improved_prompt = response.text
        if not improved_prompt:
            print("\n[ERROR] El modelo devolvió una respuesta vacía al optimizar el prompt.")
            sys.exit(1)

        improved_prompt = parse_custom_prompt(improved_prompt)

        # Construir el contenido Markdown de salida
        md_content = f"""# Prompt de Optimización de CV Mejorado por IA

Este archivo contiene el prompt de optimización adaptado dinámicamente para corregir las alucinaciones detectadas en la validación anterior. Puedes leerlo, modificarlo manualmente y usarlo para regenerar tu CV optimizado.

## ¿Cómo ejecutar la optimización con este prompt?
Para usar este prompt personalizado en tu próxima optimización, ejecuta la siguiente instrucción en tu consola:

```bash
python src/cv_optimizer.py -j job_description_1.txt --prompt-file {self.output_path}
```

## Reporte de Robustez de Referencia
- **Origen del reporte**: `{self.report_path}`
- **Puntuación original**: {puntuacion_general}/10.0
- **Veredicto**: {veredicto}
- **Fecha de optimización de prompt**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        if alucinaciones:
            md_content += "\n### Alucinaciones que se buscaron resolver:\n"
            for a in alucinaciones:
                md_content += f"- **{a.get('campo')}** ({a.get('tipo')}): {a.get('explicacion')}\n"

        if recomendaciones:
            md_content += "\n### Recomendaciones aplicadas:\n"
            for rec in recomendaciones:
                md_content += f"- {rec}\n"

        md_content += f"""
---

## Instrucciones y Contenido del Prompt
Puedes editar libremente el bloque a continuación. Asegúrate de conservar las variables entre llaves como `{{profile_yaml}}` y `{{job_description}}`.

```prompt
{improved_prompt}
```
"""

        # Guardar en archivo
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"✅ Nuevo prompt optimizado y guardado con éxito en: '{os.path.abspath(self.output_path)}'\n")
        return md_content
