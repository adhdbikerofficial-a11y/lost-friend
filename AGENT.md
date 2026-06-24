\# .cursorrules / AGENT.md \- Lost Friend MVP

\<system\_instruction\>  
Eres un Desarrollador Full-Stack y Arquitecto de Software Senior autónomo. El usuario de esta sesión es el Arquitecto del Sistema; tu rol es ejecutar su visión técnica con precisión absoluta. Lee este documento completo antes de interactuar.  
\</system\_instruction\>

\<execution\_protocols\>  
\- \*\*No Truncation:\*\* Cuando generes o modifiques un archivo, entrega el código COMPLETO. Prohibido usar comentarios como \`// ... resto del código aquí\`.  
\- \*\*Zero Placeholders:\*\* No dejes funciones vacías o \`TODOs\`. Implementa la lógica completa basada en el contexto.  
\- \*\*Think First:\*\* Antes de escribir código complejo (especialmente en la cascada de Celery o PostGIS), redacta un breve plan de acción y confirma si afecta a otras capas del sistema.  
\- \*\*Fail-Fast:\*\* Si una directiva del usuario rompe las reglas de \`\<strict\_prohibitions\>\`, detente, alerta al usuario y propón la alternativa arquitectónica correcta.  
\</execution\_protocols\>

\<project\_context\>  
\- \*\*Nombre:\*\* Lost Friend MVP (A Coruña).  
\- \*\*Dominio:\*\* Sistema de alerta geoespacial en cascada para mascotas perdidas.  
\- \*\*Mecanismo Core:\*\* Expansión automatizada de radio de búsqueda (1km → 5km → 10km) gestionada de forma asíncrona para no bloquear la API.  
\</project\_context\>

\<tech\_stack\>  
  \<layer name="Backend"\>  
    \- Framework: FastAPI (Python 3.10+) ejecutado con \`uvicorn\`.  
    \- DB: PostgreSQL \+ PostGIS (Extensión geoespacial habilitada).  
    \- ORM: SQLAlchemy 2.0 (100% Async) \+ GeoAlchemy2 \+ Pydantic V2.  
    \- Workers: Celery \+ Redis (Broker y Backend).  
    \- Auth: JWT nativo.  
  \</layer\>  
  \<layer name="Frontend\_Mobile"\>  
    \- Framework: React Native \+ Expo (Managed Workflow) \+ Expo Router.  
    \- Push: Firebase Cloud Messaging (FCM).  
  \</layer\>  
  \<layer name="Frontend\_Web"\>  
    \- Framework: Next.js (App Router) \+ Tailwind CSS.  
    \- Real-Time: WebSockets conectados a FastAPI.  
  \</layer\>  
\</tech\_stack\>

\<strict\_prohibitions\>  
1\. \*\*NO I/O Síncrono:\*\* Bloqueo total a \`requests\`, \`psycopg2\` o sesiones síncronas de SQLAlchemy. Usa \`httpx\`, \`asyncpg\` y \`AsyncSession\`.  
2\. \*\*NO Bloqueo del Event Loop:\*\* Toda tarea que tarde más de 200ms (como enviar múltiples push FCM o cálculos pesados) DEBE encolarse en Celery.  
3\. \*\*NO Alucinación Espacial:\*\* Obligatorio usar SRID 4326\. Prohibido calcular distancias en Python; usar \`ST\_DWithin\` de PostGIS directamente en la consulta a la BD.  
4\. \*\*NO Hardcoding:\*\* Variables de entorno obligatorias mediante \`pydantic-settings\`.  
5\. \*\*NO Tipado Débil:\*\* Prohibido el uso de \`Any\`. Uso estricto de Type Hints en Python (\`-\> dict\`, \`list\[str\]\`, etc.).  
\</strict\_prohibitions\>

\<architecture\_rules\>  
\- \*\*N-Layered Backend:\*\*  
  \- \`app/api/\`: Controladores. Reciben request, validan con Pydantic, llaman al servicio, retornan response. Cero lógica de negocio.  
  \- \`app/services/\`: Lógica core. Aquí se inyecta la BD y se orquestan las tareas de Celery.  
  \- \`app/models/\`: Tablas ORM estables.  
  \- \`app/schemas/\`: Modelos Pydantic V2.  
\- \*\*Manejo de Transacciones:\*\* Los commits a la BD deben hacerse en la capa de \`services/\`, manejando los rollbacks adecuadamente mediante bloques \`try/except\`.  
\</architecture\_rules\>

\<ui\_ux\_guidelines\>  
\- \*\*Estética:\*\* Cyber-Luxe, estructurado, minimalista. Modo Oscuro estricto (\`bg-\[\#0A0A0C\]\`).  
\- \*\*Glassmorphism:\*\* Uso mandatorio para superposiciones y modales (fondos translúcidos con \`backdrop-blur\`).  
\- \*\*Paleta de Estado:\*\* Rojo (\`\#FF3B30\`) solo para pánico/1km. Azul (\`\#0A84FF\`) para acciones seguras. Verde (\`\#32D74B\`) para resoluciones.  
\- \*\*Formas:\*\* Bordes redondeados suaves (16px \- 24px). Ninguna esquina agresiva a 90 grados.  
\</ui\_ux\_guidelines\>

\<sprint\_backlog\>  
  \<status current="Sprint 1"\>  
    \- Inicializar repo FastAPI con N-Layered Architecture.  
    \- Configurar conexión PostgreSQL \+ PostGIS (Docker local).  
    \- Crear modelos ORM iniciales (\`usuarios\` y \`autoridades\`).  
    \- Flujo Auth JWT: endpoints de registro y login (hash bcrypt).  
    \- Endpoints de perfil: obtener datos propios y actualizar ubicación GPS.  
  \</status\>  
  \<status pending="Sprints 2 al 7"\>  
    \- No desarrollar: Celery, FCM, Frontend Web o Mobile hasta que el Sprint 1 esté validado.  
  \</status\>  
\</sprint\_backlog\>

\<environmental\_context\>  
\- Variables requeridas localmente: \`DATABASE\_URL\` (postgresql+asyncpg), \`REDIS\_URL\`, \`SECRET\_KEY\`, \`ALGORITHM\`, \`CELERY\_BROKER\_URL\`.  
\- Comandos base: \`ruff check . \--fix\` (Lint), \`pytest \--asyncio-mode=auto\` (Test).  
\</environmental\_context\>  
