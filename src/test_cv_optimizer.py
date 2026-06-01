import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import yaml
from pydantic import ValidationError

# Importar las clases y funciones del optimizador
from cv_optimizer import (
    OptimizedCV,
    OptimizedExperience,
    OptimizedEducation,
    ContactInfo,
    load_profile,
    load_job_description,
    generate_markdown,
    generate_html,
    optimize_cv
)
from optimizer import parse_custom_prompt, DEFAULT_PROMPT_TEMPLATE

class TestCVOptimizer(unittest.TestCase):
    """
    Pruebas unitarias para validar la lógica del Optimizador de CV.
    Escrito de forma robusta e instructiva para ingenieros junior.
    """

    def setUp(self) -> None:
        """
        Configura datos de prueba iniciales antes de cada test.
        """
        self.sample_profile_data = {
            "personal_info": {
                "full_name": "Ingeniero Junior de Prueba",
                "email": "test@junior.com",
                "phone": "12345678",
                "location": "Ciudad de Prueba"
            },
            "professional_summary": "Ingeniero Junior enfocado en pruebas automatizadas.",
            "skills": ["Python", "Unit Testing"],
            "education": [
                {
                    "institution": "Universidad de Ingeniería",
                    "degree": "Ingeniería en Sistemas",
                    "period": "2020-2025",
                    "achievements": ["Promedio de 9.5"]
                }
            ],
            "experiences": [
                {
                    "company": "TestCorp",
                    "role": "QA Intern",
                    "period": "2023-2024",
                    "achievements": ["Desarrollé 10 scripts de prueba."]
                }
            ]
        }

        # Estructura simulada de respuesta de Gemini en JSON
        self.mock_llm_json_response = """{
            "full_name": "Ingeniero Junior de Prueba",
            "contact_info": {
                "email": "test@junior.com",
                "phone": "12345678",
                "location": "Ciudad de Prueba"
            },
            "professional_summary": "Ingeniero Junior altamente capacitado y enfocado en pruebas de software automatizadas avanzadas.",
            "optimized_skills": ["Python", "Unit Testing", "Pytest", "CI/CD"],
            "experiences": [
                {
                    "company": "TestCorp",
                    "role": "QA Intern (Optimizado)",
                    "period": "2023-2024",
                    "tailored_achievements": [
                        "Diseñé e implementé 10 scripts de prueba automatizados con un enfoque de código limpio.",
                        "Colaboré en la optimización de procesos de control de calidad."
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Universidad de Ingeniería",
                    "degree": "Ingeniería en Sistemas",
                    "period": "2020-2025",
                    "achievements": ["Promedio sobresaliente de 9.5", "Proyecto integrador en pruebas."]
                }
            ]
        }"""

    def test_pydantic_schema_validation(self) -> None:
        """
        Verifica que el esquema de Pydantic valide correctamente un JSON correcto.
        """
        try:
            cv = OptimizedCV.model_validate_json(self.mock_llm_json_response)
            self.assertEqual(cv.full_name, "Ingeniero Junior de Prueba")
            self.assertEqual(len(cv.optimized_skills), 4)
            self.assertEqual(cv.experiences[0].company, "TestCorp")
        except ValidationError as exc:
            self.fail(f"La validación del esquema Pydantic falló inesperadamente: {exc}")

    def test_pydantic_schema_invalid_data(self) -> None:
        """
        Verifica que Pydantic capture errores cuando falten campos obligatorios.
        """
        invalid_json = '{"full_name": "Ingeniero Junior Incompleto"}'
        with self.assertRaises(ValidationError):
            OptimizedCV.model_validate_json(invalid_json)

    def test_load_profile_success(self) -> None:
        """
        Verifica la carga exitosa de un archivo YAML válido.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as temp_file:
            yaml.dump(self.sample_profile_data, temp_file, allow_unicode=True)
            temp_file_name = temp_file.name

        try:
            loaded_data = load_profile(temp_file_name)
            self.assertEqual(loaded_data["personal_info"]["full_name"], "Ingeniero Junior de Prueba")
            self.assertEqual(loaded_data["skills"][0], "Python")
        finally:
            os.remove(temp_file_name)

    def test_load_job_description_success(self) -> None:
        """
        Verifica la lectura exitosa de una descripción de puesto desde un archivo de texto.
        """
        sample_text = "Se busca desarrollador Python con experiencia en pruebas unitarias."
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(sample_text)
            temp_file_name = temp_file.name

        try:
            loaded_text = load_job_description(temp_file_name)
            self.assertEqual(loaded_text, sample_text)
        finally:
            os.remove(temp_file_name)

    def test_generate_markdown_spanish(self) -> None:
        """
        Verifica que el generador de Markdown cree un string bien formateado en español.
        """
        cv = OptimizedCV.model_validate_json(self.mock_llm_json_response)
        markdown_output = generate_markdown(cv, lang="es")
        
        self.assertIn("# Ingeniero Junior de Prueba", markdown_output)
        self.assertIn("## Resumen Profesional", markdown_output)
        self.assertIn("QA Intern (Optimizado)", markdown_output)
        self.assertIn("Universidad de Ingeniería", markdown_output)

    def test_generate_markdown_english(self) -> None:
        """
        Verifica que el generador de Markdown use las cabeceras en inglés si se selecciona dicho idioma.
        """
        cv = OptimizedCV.model_validate_json(self.mock_llm_json_response)
        markdown_output = generate_markdown(cv, lang="en")
        
        self.assertIn("# Ingeniero Junior de Prueba", markdown_output)
        self.assertIn("## Professional Summary", markdown_output)
        self.assertIn("## Projects & Practical Experience", markdown_output)
        self.assertIn("## Education & Training", markdown_output)

    def test_generate_html_premium(self) -> None:
        """
        Verifica que el generador de HTML premium cree un archivo de marcado estructurado con estilos CSS y soporte A4.
        """
        cv = OptimizedCV.model_validate_json(self.mock_llm_json_response)
        html_output = generate_html(cv, lang="es")
        
        self.assertIn("<!DOCTYPE html>", html_output)
        self.assertIn('<html lang="es">', html_output)
        self.assertIn('<div class="resume-container">', html_output)
        self.assertIn("<h2>Resumen Profesional</h2>", html_output)
        self.assertIn("Ingeniero Junior de Prueba", html_output)
        # Comprobar la existencia de estilos de impresión claves
        self.assertIn("@media print", html_output)
        self.assertIn("page-break-inside: avoid", html_output)

    def test_parse_custom_prompt_from_markdown_block(self) -> None:
        """
        Verifica que se extraiga correctamente el bloque ```prompt de un archivo Markdown.
        """
        md_content = """# Título
Texto introductorio.

```prompt
You are a recruiter.
Profile: {profile_yaml}
Job: {job_description}
Language: {language_name} ({lang})
```
"""
        extracted = parse_custom_prompt(md_content)
        self.assertIn("You are a recruiter.", extracted)
        self.assertIn("{profile_yaml}", extracted)
        self.assertNotIn("# Título", extracted)

    def test_parse_custom_prompt_plain_text_fallback(self) -> None:
        """
        Verifica que un archivo de texto plano se use íntegramente como plantilla.
        """
        plain = "Optimize CV for {job_description} using {profile_yaml} in {language_name}."
        self.assertEqual(parse_custom_prompt(plain), plain)

    def test_default_prompt_template_has_required_placeholders(self) -> None:
        """
        Verifica que la plantilla por defecto contenga todos los placeholders del runtime.
        """
        for placeholder in ("{profile_yaml}", "{job_description}", "{language_name}", "{lang}"):
            self.assertIn(placeholder, DEFAULT_PROMPT_TEMPLATE)

    @patch("google.genai.Client")
    def test_optimize_cv_with_mock_client(self, mock_client_class) -> None:
        """
        Prueba la función de optimización simulando la respuesta de la API de Gemini.
        """
        # Configurar variables de entorno ficticias para el test
        os.environ["GEMINI_API_KEY"] = "mock_api_key_for_testing"

        # Simular el cliente de GenAI y su respuesta
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = self.mock_llm_json_response
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        try:
            cv = optimize_cv(self.sample_profile_data, "Job Description", lang="es")
            self.assertIsInstance(cv, OptimizedCV)
            self.assertEqual(cv.full_name, "Ingeniero Junior de Prueba")
            self.assertEqual(cv.experiences[0].role, "QA Intern (Optimizado)")
        finally:
            # Limpiar la variable de entorno
            del os.environ["GEMINI_API_KEY"]


if __name__ == "__main__":
    unittest.main()
