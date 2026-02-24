
# 🎟️ EventHub -- Plataforma de Ticketera (Proyecto Educativo)

EventHub es una aplicación web simplificada de venta de tickets
desarrollada con **Flask**, creada con fines educativos.

Este proyecto está diseñado para enseñar **prácticas de desarrollo
seguro**, enfocándose en autenticación, validación de entradas, manejo
de sesión y principios de codificación segura.

#Test C G

------------------------------------------------------------------------

# 📦 Estructura del Proyecto

    eventhub/
    │
    ├── app.py                # Aplicación principal Flask (rutas + lógica backend)
    ├── requirements.txt      # Dependencias de Python
    │
    ├── data/
    │   ├── events.json       # Catálogo de eventos (simula base de datos)
    │   ├── users.json        # Usuarios registrados (almacenamiento en JSON)
    │   └── orders.json       # Órdenes de compra
    │
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   ├── event_detail.html
    │   ├── login.html
    │   ├── register.html
    │   ├── checkout.html
    │   └── dashboard.html
    │
    └── static/
        └── styles.css        # Estilos globales

------------------------------------------------------------------------

# 🏗️ Arquitectura General

-   **Framework:** Flask\
-   **Motor de plantillas:** Jinja2\
-   **Almacenamiento:** Archivos JSON (sin base de datos real)\
-   **Frontend:** HTML renderizado en servidor + CSS

El proyecto sigue una estructura simple tipo MVC:

-   Lógica → `app.py`
-   Vistas → `templates/`
-   Archivos estáticos → `static/`
-   Datos → `data/*.json`

------------------------------------------------------------------------

# 🚀 Funcionalidades Implementadas

## 1️⃣ Área Pública

### 🏠 Landing (`/`)

-   Muestra eventos destacados y próximos.
-   Permite filtrar por:
    -   Palabra clave
    -   Ciudad
    -   Categoría
    -   Fecha

Fuente de datos: `events.json`

------------------------------------------------------------------------

### 🎫 Detalle del Evento (`/event/<id>`)

-   Muestra información completa del evento.
-   Permite seleccionar cantidad de tickets.
-   Botón "Buy Ticket" redirige al checkout.

------------------------------------------------------------------------

## 2️⃣ Sistema de Autenticación

### 📝 Registro (`/register`)

-   Guarda usuarios en `users.json`
-   Campos:
    -   Nombre completo
    -   Email
    -   Teléfono
    -   Contraseña
    -   Confirmación de contraseña
-   Evita registro de emails duplicados.


------------------------------------------------------------------------

### 🔐 Login (`/login`)

-   Verifica:
    -   Existencia del usuario
    -   Coincidencia de contraseña
-   Redirige al dashboard tras autenticarse.


------------------------------------------------------------------------

## 3️⃣ Dashboard (`/dashboard`)


Muestra: - Mensaje de bienvenida - Confirmación de pago si aplica

------------------------------------------------------------------------

## 4️⃣ Flujo de Checkout

### Paso 1: Buy Ticket

`POST /event/<id>/buy` - Valida cantidad contra disponibilidad -
Redirige a checkout

### Paso 2: Checkout

`GET /checkout/<id>?qty=N`

Muestra: - Resumen de orden - Desglose de precios - Formulario de pago

### Paso 3: Pago

`POST /checkout/<id>` - Guarda orden en `orders.json` - Redirige al
dashboard

------------------------------------------------------------------------

# 🗃️ Capa de Datos (Archivos JSON)

### events.json

Contiene el catálogo de eventos.

### users.json

Usuarios registrados:

``` json
{
  "id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "123456",
  "password": "plaintext"
}
```

### orders.json

Órdenes de compra:

``` json
{
  "id": 1,
  "user_email": "john@example.com",
  "event_id": 3,
  "qty": 2,
  "total": 155.00,
  "status": "PAID"
}
```

------------------------------------------------------------------------

# 🔄 Flujo General de la Aplicación

    Landing → Detalle Evento → Buy Ticket → Checkout → Pago → Dashboard

Flujo de autenticación:

    Registro → Login → Creación de sesión → Acceso a páginas protegidas

------------------------------------------------------------------------

# 🛠️ Cómo Ejecutar

``` bash
pip install -r requirements.txt
python app.py
```

Abrir en navegador:

    http://127.0.0.1:5000

------------------------------------------------------------------------

# 🚀 Próximos Laboratorios

-   Implementar hashing de contraseñas
-   Agregar roles (User / Organizer / Admin)
-   Transferencia de tickets
-   Validación centralizada
