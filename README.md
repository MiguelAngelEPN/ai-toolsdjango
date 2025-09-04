# ai-toolsdjango

Monorepo con dos proyectos:

- **`djangoai/`** – Backend **Django + DRF** con un endpoint de asistente que usa **Ollama** (modelos locales) a través del SDK de `openai`.
- **`frontai/`** – Frontend **Next.js**.

---

## Estructura
ai-toolsdjango/
├── djangoai/ # Backend (Django + DRF + Ollama)
└── frontai/ # Frontend (Next.js)

---

## Requisitos

- **Python 3.10+**
- **Node.js 18+** (recomendado 20+)
- **Git**
- **Ollama** instalado y ejecutándose localmente

### Instalar y preparar Ollama

- Windows (PowerShell):

```powershell
winget install Ollama.Ollama
ollama serve
```

## Descargar un modelo compatible
```powershell
ollama pull qwen2.5
```

# opcional:
```powershell
ollama pull llama3.1
```

## Guía de inicio rápido
# 1) Clonar el repo
```powershell
git clone https://github.com/MiguelAngelEPN/ai-toolsdjango.git
cd ai-toolsdjango
```

# 2) Levantar backend
```powershell
cd djangoai
python -m venv .venv
```
# Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```
# Git Bash:
```powershell
source .venv/Scripts/activate
pip install -r requirements.txt  
python manage.py migrate
python manage.py runserver
```
# Backend en http://127.0.0.1:8000

# 3) Levantar frontend
```powershell
cd ../frontai
npm install
npm run dev
```
# Front en http://localhost:3000
