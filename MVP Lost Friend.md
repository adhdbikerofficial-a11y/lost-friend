# MVP Lost Friend 

# Requerimientos minimos del MVP 

## El problema 

 Actualmente en la ciudad de coruna españa se ve un alarmante problema donde el proceso actual de aviso de mascotas perdidas es lento y no integra de manera activa a la comunidad . las autoridades pertinentes pierden hasta 2 horas entre que el animal se pierde hasta emitir la orden de búsquedas además de que la información no llega completa y entorpece las búsquedas o provoca confusiones al buscar.

## El usuario

El usuario final son los dueños de mascotas y las autoridades y empresas que trabajan la para la junta de galicia.

## La solucion minima

La solución mínima para estos problemas de integración , tiempo e información es un sistema de registro de mascotas que permita a los usuarios enviar la alarma de mascota pérdida de manera inmediata , tanto a los interesados en animales de alrededor como a las autoridades pertinentes de manera secuencial (buscamos que sea secuencial debido a que si envías una alerta general podría ser agitar a mucha gente por algo que se podría resolver con las personas de tu alrededor)

## La métrica de éxito 

Usuarios activos en la aplicación 

## Matriz de priorización

## 

| Feature | Valor usuario | Esfuerzo |
| :---- | :---- | :---- |
| Login | alto | bajo |
| registro | alto | medio |
| Tienda | bajo | medio |
| Grupo familiar | bajo | medio |
| Alarma | medio | alto |

User journey

| Fases | Login | Inicio de alerta | Ingreso de clave única | Primer radio de busqueda | Segundo radio de búsqueda | Tercer radio de búsqueda | Notificación de hallazgo | Verificacion de mascota recuperada |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| Objetivo | Se espera que el usuario pueda ingresar directamente a la aplicación con usuario y clave | se espera que al momento de presionar el "Boton de Panico" se detecte la ubicacion del usuario | se espera que se abra una ventana emergente que advierta que para lanzar la alerta de mascota perdida y alertar a las autoridades pertinentes , se debe ingresar la clave unica de mascota perdida asociada a su mascota | se espera que en la posicion de la alerta se dibuje en el mapa un circulo de un 1km de radio que represente el proceso de envio de alrtas a los telefonos dentro de esa area que tengan la aplicacion | Se espera que al pasar X canidad de tiempo se dibuje en el mapa otro circulo de otro color por encima del primero que ahora tenga un radio de 5 kilometros en el mapa que represente que ahora que no decteto que alguien lo vio , esta avisando mas lejos para que mas personas sepan del animal y logren encontrar rapido a la mascota | se espera que ahora despues de otro tiempo X aparezca otro circulo de radio de 10km o avsar a todos los usuarios registrados en esa ciudad , sobre el animal esperando que alguien responda | al momento de que alguien o las autoridades avisen de que tienen a la mascota al usuario se le quitaran los circulos del mapa y le saldra la localizacion de donde esta la mascota en el mapa . | al dar clikc en el boton de verificar se pedira que el due;o responda algunas pregntas ademas de proporcionar una foto del animal (pcional) para terminar el proceso de alerta y se le avise a los interesados que el animal esta a salvo |
| Actividad |  |  |  |  |  |  |  |  |
| Puntos de contacto | Telefono | Telefono | Telefono | Telefono | Telefono | Telefono | Telefono | Telefono |
| Sensaciones | Estres y preocupacionpor la situacion de la mascota perdida | Estres y preocupacionpor la situacion de la mascota perdida | Estres y preocupacionpor la situacion de la mascota perdida | se busca que esa angustia y nervios disminuyan al mostrar qu emas gente es informada y no esta solo | se busca que esa angustia y nervios disminuyan al mostrar qu emas gente es informada y no esta solo | se busca que esa angustia y nervios disminuyan al mostrar qu emas gente es informada y no esta solo | se busca que al resivir la noicia se verifique que es correcto y dar la informacion de manera que el usuario se sienta tranquilo al saber que su mascota fue encontrada | calma y tranquilidad para responder de mejor manera las preguntas y pueda ser de ayuda en un futuro |
| Conclusiones |  |  |  |  |  |  |  |  |

## Stack tegnologico

* Mobile \= React Native \+ Expo  
* Web \= [Next.js](http://Next.js)   
* Backend \= Fast API   
* Base de Datos \= PostgreSQL  
* Colas \= Redis \+ Celery  
* Notificaciones \= Firebase Cloud Messaging  
* Tiempo Real \= WebSockets (FastAPI)  
* Infraestructura \= Railway  
* Versiones \= Git / Githubs

# Arquitectura minima 

## Entidades de datos 

Usuarios

| ID | Nombre | Telefono | Correo Electronico | ID Grupo Familiar  | Confirmación de lectura  |
| :---- | :---- | :---- | :---- | :---- | :---- |

Mascotas 

| ID | IDusuario | codigo | nombre | especie | raza | sexo | Fecha  nacimiento | Color pelaje | Rasgos distintivos |  ID Grupo familiar |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |

Grupo familiar

| ID | Creador(ID usurio) | Personas | Mascotas  |
| :---- | :---- | :---- | :---- |

## Acciones principales 

Por definir 

## Autenticacion

Por definir   
