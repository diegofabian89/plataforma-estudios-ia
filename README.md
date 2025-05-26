# EdukAI – Plataforma Inteligente para la Gestión de Apuntes
<img src="static/img/logo_frontal.png" alt="EdukAI Logo" width="150"/>  

> Plataforma web educativa potenciada por Inteligencia Artificial que permite a los estudiantes subir apuntes, generar resúmenes automáticos, crear preguntas tipo test, y organizar su contenido de estudio de forma eficiente y personalizada.

---

##  Funcionalidades principales

-  Subida de apuntes en formato PDF o texto plano.
-  Generación de resúmenes automáticos usando IA.
-  Creación de preguntas de estudio tipo test.
-  Organización automática de apuntes por categorías.
-  Descarga de resúmenes y tests en formato PDF.
-  Realización de autoevaluaciones con puntuación guardada.
-  Panel de usuario con gestión de perfil y visualización de progreso.
-  Sistema de autenticación y gestión de usuarios.
-  Diseño responsive con estilo moderno y accesible.

---

##  Tecnologías utilizadas

### Backend:
- Python
- Django + FastAPI
- PostgreSQL

### IA y NLP:
- OpenAI GPT-4
- spaCy y transformers

### Frontend:
- HTML5, CSS3, JavaScript
- Bootstrap

### Otros:
- PyPDF2 – extracción de texto
- ReportLab – generación de PDF
- AWS S3 – almacenamiento de archivos (opcional)
- GitHub – control de versiones

---

##  Instalación local

1. Clona el repositorio:
   ```bash
   gh repo clone diegofabian89/plataforma-estudios-ia
   cd edukai
   ```

2. Crea un entorno virtual e instala dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```

3. Aplica migraciones y ejecuta el servidor:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. Accede desde: `http://127.0.0.1:8000/`

---

##  Estructura del proyecto

```
edukai/
├── backend/              # Lógica Django y APIs FastAPI
├── frontend/             # Plantillas HTML, CSS, JS
├── media/                # Archivos subidos por el usuario
├── static/               # Archivos estáticos
├── templates/            # Interfaces visuales
├── tests/                # Pruebas unitarias
├── requirements.txt
└── README.md
```

---

##  Planificación y Gantt

Consulta el progreso del proyecto y su planificación en el [Diagrama de Gantt](https://github.com/tuusuario/edukai/gantt](https://github.com/diegofabian89/plataforma-estudios-ia/blob/main/documentation/Screenshot%202025-05-26%20180725.png).

---

##  Casos de uso y testing

- Test de carga de documentos
- Test de precisión en resúmenes generados
- Validación de preguntas creadas
- Pruebas de sesión, permisos y funcionalidades para invitados

---

##  Presupuesto

- Horas estimadas: 162 h
- Coste estimado de desarrollo: 4.085 €
- Inversión en OpenAI: 5 €
- Infraestructura: uso local y/o AWS (~30 €/mes estimado)

---

##  Licencia

Proyecto académico realizado como parte del Ciclo Formativo de Grado Superior en **Desarrollo de Aplicaciones Multiplataforma (DAM)**.  
Uso educativo – Todos los derechos reservados © 2025.

---

##  Contacto

**DIEGO FABIAN**  
Email: diegofabian1989@hotmail.es  

GitHub: [@diegofabian89](https://github.com/diegofabian89/plataforma-estudios-ia.git)
