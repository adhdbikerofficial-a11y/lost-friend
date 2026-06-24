# 🐾 Lost Friend MVP

> Sistema de alerta geoespacial en cascada para mascotas perdidas — A Coruña, España.

---

## ¿Qué es Lost Friend?

Lost Friend es una plataforma móvil y web que permite a los dueños de mascotas disparar una alerta de emergencia con un solo botón. La alerta notifica en tiempo real a los usuarios cercanos en un radio creciente (1 km → 5 km → 10 km) y simultáneamente informa a las autoridades locales a través de un dashboard exclusivo. El objetivo es reducir el tiempo de respuesta de búsqueda de 2 horas (proceso actual) a minutos.

---

## Estado del proyecto

| Sprint | Descripción | Estado |
|--------|-------------|--------|
| Sprint 1 | Base de infraestructura y autenticación JWT | 🔄 En curso |
| Sprint 2 | Core geoespacial y tareas diferidas (Celery) | ⏳ Pendiente |
| Sprint 3 | Notificaciones push (Firebase FCM) | ⏳ Pendiente |
| Sprint 4 | App móvil (React Native + Expo) | ⏳ Pendiente |
| Sprint 5 | Dashboard web de autoridades (Next.js) | ⏳ Pendiente |
| Sprint 6 | Flujo de resolución y verificación | ⏳ Pendiente |
| Sprint 7 | QA, errores y refinamiento final | ⏳ Pendiente |

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────┐
│                    CLIENTES                         │
│  📱 React Native + Expo   💻 Next.js (Autoridades) │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS / WebSocket (JWT)
┌──────────────────────▼──────────────────────────────┐
│              ⚡ FastAPI Backend                      │
│         API REST asíncrona + WebSockets             │
└────────┬──────────────────────────┬─────────────────┘
         │                          │
┌────────▼──────────┐   ┌───────────▼──────────────────┐
│ 🐘 PostgreSQL     │   │  🔴 Redis + ⚙️ Celery        │
│    + PostGIS      │   │  Cascada: T+0 → T+X → T+Y   │
│ (consultas geo    │   └───────────┬──────────────────┘
│  ST_DWithin)      │               │
└───────────────────┘   ┌───────────▼──────────────────┐
                        │  🔥 Firebase FCM             │
                        │  Push → Android + iOS        │
                        └──────────────────────────────┘
```

---

## Stack tecnológico

### Backend
- **FastAPI** (Python 3.10+) — API REST asíncrona + WebSockets
- **SQLAlchemy 2.0** (AsyncSession) + **GeoAlchemy2** — ORM 100% async
- **PostgreSQL + PostGIS** — Base de datos con consultas geoespaciales
- **Redis + Celery** — Cola de tareas para la cascada de alertas diferidas
- **python-jose + passlib[bcrypt]** — Autenticación JWT

### Frontend Mobile
- **React Native + Expo** (Managed Workflow) — iOS y Android desde un codebase
- **Expo Router** — Navegación basada en archivos
- **Firebase Cloud Messaging** — Notificaciones push nativas

### Frontend Web (Autoridades)
- **Next.js** (App Router) — Dashboard en tiempo real
- **Tailwind CSS** — Estilos con tema Cyber-Luxe / Dark Mode

### Infraestructura
- **Railway** — Deploy inicial (MVP)
- **Git / GitHub** — Control de versiones
- **AWS** (RDS + ElastiCache + ECS) — Destino de migración en escala

---

## Cuentas externas requeridas

Estos tres servicios externos requieren registro previo al desarrollo:

### 1. GitHub — Control de versiones
- **Cuándo:** Antes de escribir la primera línea de código
- **Por qué:** Repositorio del proyecto y colaboración con el agente de IA
- **Registro:** https://github.com
- **Costo:** Gratis

### 2. Firebase — Notificaciones push (FCM)
- **Cuándo:** Sprint 3 (pero conviene crearlo antes para tenerlo listo)
- **Por qué:** Firebase Cloud Messaging es la única API que entrega notificaciones push a Android e iOS con una sola integración
- **Pasos de configuración:**
  1. Ir a https://console.firebase.google.com
  2. Crear proyecto → nombre: `lost-friend`
  3. Activar **Cloud Messaging** en el panel
  4. Ir a Configuración del proyecto → Cuentas de servicio
  5. Generar nueva clave privada → descargar `firebase-adminsdk.json`
  6. Guardar ese archivo en `backend/config/firebase-adminsdk.json`
  7. Añadir `config/firebase-adminsdk.json` al `.gitignore`
- **Costo:** Gratis (tier Spark cubre millones de notificaciones/mes)

### 3. Railway — Deploy en la nube
- **Cuándo:** Final del Sprint 1
- **Por qué:** Plataforma de deploy que soporta FastAPI + PostgreSQL + Redis con configuración mínima
- **Pasos de configuración:**
  1. Ir a https://railway.app
  2. Conectar con cuenta de GitHub
  3. Crear nuevo proyecto → `lost-friend-backend`
  4. Añadir servicio PostgreSQL (Railway lo provee gestionado)
  5. Añadir servicio Redis (Railway lo provee gestionado)
  6. Conectar el repositorio de GitHub para deploy automático
  7. Copiar las variables de entorno del `.env` al panel de Railway
- **Costo:** Gratis hasta ~500 horas de ejecución/mes (suficiente para MVP)

> **Nota:** Todo lo demás (PostgreSQL, Redis, FastAPI, Next.js, React Native) corre localmente en tu máquina. No necesitas más cuentas externas para desarrollar.

---

## Instalación local (sin Docker)

Este proyecto está configurado para correr directamente sobre el sistema operativo Linux sin necesidad de virtualización ni contenedores.

### Requisitos del sistema

```bash
# Verificar versiones mínimas
python3 --version    # 3.10+
node --version       # 18+
psql --version       # 14+
redis-cli --version  # 6+
```

### 1. Instalar PostgreSQL + PostGIS

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgis

# Iniciar el servicio
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Crear base de datos y habilitar PostGIS
sudo -u postgres psql -c "CREATE USER lost_friend WITH PASSWORD 'lost_friend_pass';"
sudo -u postgres psql -c "CREATE DATABASE lost_friend_db OWNER lost_friend;"
sudo -u postgres psql -d lost_friend_db -c "CREATE EXTENSION postgis;"

# Verificar que PostGIS está activo
sudo -u postgres psql -d lost_friend_db -c "SELECT PostGIS_version();"
```

### 2. Instalar Redis

```bash
sudo apt install -y redis-server

# Iniciar el servicio
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verificar que responde
redis-cli ping   # Debe responder: PONG
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/lost-friend-backend.git
cd lost-friend-backend
```

### 4. Configurar el entorno Python

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

```bash
# Copiar plantilla
cp env.example .env

# Generar SECRET_KEY segura
openssl rand -hex 32
# Copiar el resultado y pegarlo en SECRET_KEY dentro de .env

# Editar el archivo .env con tus valores reales
nano .env
```

Variables críticas que debes completar en `.env`:

```env
DATABASE_URL=postgresql+asyncpg://lost_friend:lost_friend_pass@localhost:5432/lost_friend_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
SECRET_KEY=<resultado del openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
ALERT_EXPAND_5KM_MINUTES=10
ALERT_EXPAND_10KM_MINUTES=30
```

### 6. Iniciar el backend

```bash
# Activar entorno virtual si no está activo
source venv/bin/activate

# Iniciar FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`
Documentación interactiva: `http://localhost:8000/docs`

### 7. Iniciar Celery (cuando llegues al Sprint 2)

```bash
# En una terminal separada, con el venv activo
celery -A app.core.celery_app worker --loglevel=info
```

---

## Estructura del proyecto

```
lost-friend-backend/
│
├── app/
│   ├── api/              # Controladores — reciben request, validan, retornan response
│   │   ├── auth.py
│   │   ├── usuarios.py
│   │   ├── mascotas.py
│   │   └── alertas.py
│   │
│   ├── services/         # Lógica de negocio — BD, Celery, reglas del dominio
│   │   ├── auth_service.py
│   │   ├── usuario_service.py
│   │   ├── mascota_service.py
│   │   └── alerta_service.py
│   │
│   ├── models/           # Tablas ORM (SQLAlchemy 2.0 + GeoAlchemy2)
│   │   ├── usuario.py
│   │   ├── mascota.py
│   │   ├── alerta.py
│   │   └── autoridad.py
│   │
│   ├── schemas/          # Modelos Pydantic V2 — validación de datos
│   │   ├── auth.py
│   │   ├── usuario.py
│   │   ├── mascota.py
│   │   └── alerta.py
│   │
│   └── core/             # Configuración transversal
│       ├── config.py     # pydantic-settings — lee el .env
│       ├── database.py   # AsyncSession + engine
│       ├── security.py   # JWT + bcrypt
│       └── celery_app.py # Instancia Celery (Sprint 2)
│
├── tests/
│   ├── test_auth.py
│   └── test_alertas.py
│
├── config/
│   └── firebase-adminsdk.json   # ← NO subir a Git (.gitignore)
│
├── main.py              # Punto de entrada FastAPI
├── requirements.txt
├── .env                 # ← NO subir a Git (.gitignore)
├── .gitignore
└── README.md
```

---

## Tiempos de la cascada de alertas

Configurables mediante variables de entorno (sin tocar código):

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `ALERT_EXPAND_5KM_MINUTES` | `10` | Minutos desde la alerta inicial hasta expandir a 5 km |
| `ALERT_EXPAND_10KM_MINUTES` | `30` | Minutos desde la alerta inicial hasta expandir a 10 km |

---

## Paleta de estados de alerta

| Estado | Color | Significado |
|--------|-------|-------------|
| `ACTIVA_1KM` | `#FF3B30` Rojo | Alerta recién disparada, radio de 1 km |
| `ACTIVA_5KM` | Naranja | Sin respuesta, expandida a 5 km |
| `ACTIVA_10KM` | Amarillo | Sin respuesta, expandida a 10 km |
| `RESUELTA` | `#32D74B` Verde | Mascota encontrada y verificada |
| `CANCELADA` | Gris | Cancelada por el dueño |

---

## Comandos de desarrollo

```bash
# Lint y formato de código
ruff check . --fix

# Ejecutar tests
pytest --asyncio-mode=auto

# Ver logs de Redis
redis-cli monitor

# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Verificar estado de Redis
sudo systemctl status redis-server
```

---

## Reglas del agente de IA (resumen)

Este proyecto usa un agente de IA para acelerar el desarrollo. Las reglas completas están en `AGENT.md`. Resumen de prohibiciones estrictas:

- ❌ No I/O síncrono — usar `httpx`, `asyncpg`, `AsyncSession`
- ❌ No bloquear el event loop — tareas largas van a Celery
- ❌ No calcular distancias en Python — usar `ST_DWithin` de PostGIS
- ❌ No hardcoding — todo configurable vía `.env`
- ❌ No tipado débil — type hints estrictos, prohibido `Any`

---

## Documentación del proyecto

| Archivo | Contenido |
|---------|-----------|
| `AGENT.md` | Reglas de comportamiento del agente de IA |
| `ARCHITECTURE.md` | Topología del sistema y diagrama de componentes |
| `SPRINT_BACKLOG.md` | Estado actual del desarrollo por sprint |
| `UI_UX_GUIDELINES.md` | Sistema de diseño Cyber-Luxe / Dark Mode |
| `env.example` | Plantilla de variables de entorno |

---

*Lost Friend — Documento vivo. Actualizar al cierre de cada sprint.*
