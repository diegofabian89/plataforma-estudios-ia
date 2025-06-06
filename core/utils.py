import datetime

import PyPDF2
from django.core.cache import cache

from openai import OpenAI

from decouple import config

client = OpenAI(api_key=config('OPENAI_API_KEY'))


def resumir_texto_con_ia(texto):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente que resume textos académicos para estudiantes."},
            {"role": "user", "content": f"Resume este texto en español:\n\n{texto}"}
        ],
        max_tokens=1500
    )
    return respuesta.choices[0].message.content.strip()


def extraer_texto_de_pdf(pdf_file):
    texto = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            texto += page.extract_text() or ""
    except PyPDF2.errors.PdfReadError:

        return None

    texto_limpio = texto.strip()
    if not texto_limpio:
        return None
    return texto_limpio


def predecir_categoria_con_ia(texto):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Eres un asistente de clasificación de documentos educativos."
                "Clasifica el siguiente texto en una de estas categorías: Matemáticas, Historia, Programación, Literatura, Filosofía, Física, Química, Geografía, Biología, Idiomas, Educación Física."
                "Si no encaja, sugiere una categoría nueva pero concreta (no general). Devuelve solo el nombre de la categoría."
            )},
            {"role": "user", "content": f"Texto:\n\n{texto}"}
        ],
        max_tokens=40
    )
    return respuesta.choices[0].message.content.strip()


def generar_titulo_con_ia(texto):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "Eres un asistente de clasificación de documentos educativos."
                "Genera un título breve y claro para un apunte académico basado en el siguiente contenido."
                "El título debe ser breve, descriptivo y en español y sin la etiqueta Titulo: solo el texto generado."
            )},
            {"role": "user", "content": f"Texto:\n\n{texto}"}
        ],
        max_tokens=30
    )
    return respuesta.choices[0].message.content.strip()


def generar_preguntas_con_ia(texto):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "Eres un asistente para estudiantes. Crea 15 preguntas tipo test de 4 opciones sobre el "
                        "siguiente texto. Devuelve **SOLAMENTE** un array JSON válido que contenga los objetos de las "
                        "preguntas en el siguiente formato: [{\"pregunta\": \"...\", \"opciones\": [\"...\", \"...\", "
                        "\"...\", \"...\"], \"respuesta_correcta\": \"...\"}]. **No incluyas ningún otro texto antes "
                        "o después del JSON.**"},
            {"role": "user", "content": texto}
        ],
        temperature=0.7,
        max_tokens=2500
    )
    return respuesta.choices[0].message.content.strip()


def generar_consejo_diario_con_cache(user_id, estudio_actual,user_name):
    hoy = datetime.date.today()
    cache_key = f"consejo_ia_{user_id}_{hoy.isoformat()}"
    consejo = cache.get(cache_key)

    if consejo:
        return consejo

    # Generar nuevo consejo
    prompt = (f"Dame un consejo breve  para estudiantes de {estudio_actual} con nombre {user_name}. Solo dos párrafos. Fecha: "
              f"{hoy.strftime('%d/%m/%Y')}. No uses saludos ni introducciones, "
              f"solo da directamente el consejo empezando con el nombre del estudiante solo el primer nombre.")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente educativo que da consejos útiles."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.8
    )

    consejo_generado = response.choices[0].message.content.strip()

    cache.set(cache_key, consejo_generado, 60 * 60 * 24)

    return consejo_generado
