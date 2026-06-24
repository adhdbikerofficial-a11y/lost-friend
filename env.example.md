\# \==========================================  
\# LOST FRIEND MVP \- ENVIRONMENT VARIABLES  
\# \==========================================  
\# Renombra este archivo a .env y completa los valores reales  
\# NUNCA subas el archivo .env al control de versiones (asegura que esté en .gitignore)

\# \------------------------------------------  
\# CONFIGURACIÓN DEL ENTORNO (FASTAPI)  
\# \------------------------------------------  
ENVIRONMENT=development  
DEBUG=True  
API\_HOST=0.0.0.0  
API\_PORT=8000

\# \------------------------------------------  
\# BASE DE DATOS (POSTGRESQL \+ POSTGIS)  
\# \------------------------------------------  
\# Formato: postgresql+asyncpg://usuario:password@host:puerto/nombre\_db  
DATABASE\_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lost\_friend\_db

\# \------------------------------------------  
\# COLAS Y TAREAS EN SEGUNDO PLANO (REDIS \+ CELERY)  
\# \------------------------------------------  
REDIS\_URL=redis://localhost:6379/0  
CELERY\_BROKER\_URL=redis://localhost:6379/1  
CELERY\_RESULT\_BACKEND=redis://localhost:6379/2

\# \------------------------------------------  
\# SEGURIDAD Y AUTENTICACIÓN (JWT)  
\# \------------------------------------------  
\# Generar una clave segura usando: openssl rand \-hex 32  
SECRET\_KEY=tu\_super\_clave\_secreta\_aqui\_no\_usar\_en\_produccion  
ALGORITHM=HS256  
ACCESS\_TOKEN\_EXPIRE\_MINUTES=1440 \# 24 horas  
REFRESH\_TOKEN\_EXPIRE\_DAYS=30

\# \------------------------------------------  
\# NOTIFICACIONES PUSH (FIREBASE CLOUD MESSAGING)  
\# \------------------------------------------  
\# Ruta absoluta o relativa al archivo JSON de credenciales de servicio de Firebase  
FIREBASE\_CREDENTIALS\_PATH=./config/firebase-adminsdk.json

\# \------------------------------------------  
\# INFRAESTRUCTURA ESCALA (AWS / RAILWAY)  
\# \------------------------------------------  
\# Variables reservadas para futuros despliegues  
\# AWS\_REGION=eu-west-3  
\# AWS\_ACCESS\_KEY\_ID=  
\# AWS\_SECRET\_ACCESS\_KEY=  
