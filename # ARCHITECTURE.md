\# ARCHITECTURE.md \- Lost Friend MVP

\*\*Instrucción para el Agente:\*\* Este documento describe la topología del sistema y el flujo de datos principal. Usa esta referencia para entender cómo interactúan los componentes antes de escribir código de integración o lógica de negocio.

\#\# 1\. Topología del Sistema (C4 Model \- Nivel Contenedor)

El sistema se divide en 5 capas principales que operan de forma asíncrona:

\* \[cite\_start\]\*\*Capa de Presentación (Client):\*\* \* App Móvil (React Native \+ Expo) para los dueños de mascotas\[cite: 10, 24\].  
    \* \[cite\_start\]Dashboard Web (Next.js) exclusivo para autoridades locales\[cite: 11, 24\].  
\* \[cite\_start\]\*\*Capa API (Gateway & Core):\*\* \* Backend en FastAPI (Python) manejando peticiones REST asíncronas y WebSockets\[cite: 24\].  
\* \*\*Capa de Datos (Storage):\*\* \* PostgreSQL \+ PostGIS. \[cite\_start\]PostGIS es crítico para realizar consultas geoespaciales por radio en milisegundos\[cite: 24\].  
\* \[cite\_start\]\*\*Capa de Tareas en Segundo Plano (Workers):\*\* \* Redis (Broker y Backend de resultados) \+ Celery\[cite: 24\]. \[cite\_start\]Encargados exclusivos de la cascada de alertas (1→5→10 km)\[cite: 24\].  
\* \[cite\_start\]\*\*Servicios Externos:\*\* \* Firebase Cloud Messaging (FCM) para notificaciones push multiplataforma\[cite: 24\].

\#\# 2\. Diagrama de Arquitectura de Alto Nivel

\`\`\`mermaid  
graph TD  
    %% Clientes  
    Mobile\[📱 React Native App\\n(Dueños y Comunidad)\]  
    Web\[💻 Next.js Dashboard\\n(Autoridades)\]

    %% API  
    API\[⚡ FastAPI Backend\\nREST \+ WebSockets\]

    %% Capa de Datos y Colas  
    DB\[(🐘 PostgreSQL \+ PostGIS)\]  
    Redis\[(🔴 Redis)\]  
    Celery\[⚙️ Celery Workers\]

    %% Servicios Externos  
    FCM\[🔥 Firebase Cloud Messaging\]

    %% Flujos  
    Mobile \<--\>|JWT / REST| API  
    Web \<--\>|JWT / WebSockets| API  
    API \<--\>|SQL Async / ST\_DWithin| DB  
    API \--\>|Encola tareas (T+X, T+Y)| Redis  
    Redis \--\>|Consume| Celery  
    Celery \<--\>|Actualiza Estado| DB  
    Celery \--\>|Dispara Notificaciones| FCM  
    FCM \--\>|Push| Mobile  
