\# SPRINT\_BACKLOG.md \- Lost Friend MVP

\*\*Instrucción para el Agente:\*\* Este documento define el estado actual del desarrollo. NO debes implementar características de Sprints futuros hasta que el Sprint "EN CURSO" esté 100% completado y verificado. Al finalizar una sesión de código, actualiza el estado de las casillas \`\[ \]\` a \`\[x\]\`.

\#\# ✅ Sprint 1: Base de Infraestructura y Autenticación (COMPLETADO)  
\*\*Objetivo:\*\* Configurar la base de datos, backend, endpoints de autenticación JWT y despliegue inicial.

\- \[x\] Inicializar repositorio de FastAPI estructurado según AGENTS.md (N-Layered Architecture).  
\- \[x\] Configurar conexión a PostgreSQL \+ PostGIS.  
\- \[x\] Implementar modelos de datos iniciales (\`usuarios\` y \`autoridades\`).  
\- \[x\] Implementar hashing de contraseñas (bcrypt) y generación de tokens JWT.  
\- \[x\] Crear endpoints: \`POST /auth/registro\` y \`POST /auth/login\`.  
\- \[x\] Crear endpoints: \`GET /usuarios/yo\` y \`PUT /usuarios/yo/ubicacion\`.  
\- \[x\] Despliegue inicial de prueba en Railway.

\---

\#\# 📅 Sprints Futuros (Pendientes)

\#\#\# ✅ Sprint 2: Core Geoespacial y Tareas Diferidas (COMPLETADO)  
\- \[x\] Configurar Redis y Celery.  
\- \[x\] Crear tabla de \`mascotas\` y generar \`codigo\_emergencia\`.  
\- \[x\] Crear tabla de \`alertas\` y lógica de estado (\`ACTIVA\_1KM\`, etc.).  
\- \[x\] Endpoint \`POST /alertas\` para disparar alerta en 1km e iniciar cascada.

\#\#\# ✅ Sprint 3: Notificaciones Push (FCM) (COMPLETADO)  
\- \[x] Integrar Firebase Cloud Messaging en FastAPI.  
\- \[x] Crear tarea Celery para expandir radio a 5km y notificar.  
\- \[x] Crear tarea Celery para expandir radio a 10km y notificar.

### ✅ Prerrequisito Sprint 4: Endpoint FCM Token (COMPLETADO)  
\- \[x] Endpoint PUT /usuarios/yo/fcm-token para que la app registre su token push.

\#\#\# Sprint 4: App Móvil (React Native)  
### ✅ Configuración inicial (COMPLETADO)  
\- \[x] Proyecto Expo + TypeScript creado en carpeta separada lost-friend-mobile/  
\- \[x] Git init con commit inicial  

### Sprint 4: App Móvil (React Native) — EN CURSO  
### ✅ Configuración inicial (COMPLETADO)  
\- \[x] Proyecto Expo + TypeScript creado en carpeta separada lost-friend-mobile/  
\- \[x] Git init con commit inicial  
\- \[x] Expo Router con navegación y auth persistence  
\- \[x] Login y registro conectados al backend  
\- \[x] Botón de pánico con especie selector + ubicación real  
\- \[x] Mapa con círculos de expansión (1km, 5km, 10km) y GPS  

### Pendiente Sprint 4:  
\- \[ \] Selector de mascota registrada del usuario  
\- \[ \] Mostrar alertas activas en el mapa desde el backend

\#\#\# Sprint 5: Dashboard Web (Next.js)  
\- \[ \] Panel de autoridades con acceso restringido.  
\- \[ \] Integración de WebSockets (\`/ws/alertas\`) para actualizaciones en vivo.

\#\#\# Sprint 6: Flujo de Resolución  
\- \[ \] Endpoints de hallazgo y cancelación (\`PUT /alertas/{id}/resolver\`).  
\- \[ \] UI para verificación de identidad de la mascota.

\#\#\# Sprint 7: QA y Refinamiento  
\- \[ \] Manejo exhaustivo de errores, refinamiento UX y QA global.  
