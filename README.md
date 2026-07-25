# API Django - Sistema Venta de Numeros

Backend inicial para autenticacion, sorteos, ventas y ganadores del sistema de vendedores.

## Requisitos

- Python 3.11+
- MySQL 8+
- pip

## Instalacion

```powershell
cd "F:\SISTEMA_VENTA_NUMEROS\API DJANGO"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuracion

Copia `.env.example` a `.env` y completa las variables reales:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TIME_ZONE=America/Guatemala

DB_NAME=sistema_venta_numeros
DB_USER=
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

No se incluyen credenciales reales en el repositorio.

Para esta fase se puede crear `.env` desde `.env.example`, pero `DB_USER` y `DB_PASSWORD` deben llenarse con credenciales reales de MySQL antes de migrar.

## Probar Conexion MySQL

El proyecto incluye un script seguro que no imprime contrasenas:

```powershell
python scripts\check_mysql_connection.py
```

Si falta configuracion, mostrara exactamente que variable falta. Ejemplo de `.env` minimo:

```env
DB_NAME=sistema_venta_numeros
DB_USER=usuario_mysql
DB_PASSWORD=contrasena_mysql
DB_HOST=127.0.0.1
DB_PORT=3306
```

Para crear la base puedes usar el script de `BASE DE DATOS MYSQL`:

```sql
SOURCE ../BASE DE DATOS MYSQL/00_database/001_create_database.sql;
```

## Migraciones

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Ejecuta `migrate` solo cuando MySQL exista y `.env` tenga credenciales validas.

## Crear superusuario

```powershell
python manage.py createsuperuser
```

## Crear Vendedor de Prueba

Despues de migrar:

```powershell
python manage.py create_test_seller
```

Credenciales de prueba para Android:

```txt
username: vendedor1
password: Vendedor123*
email: vendedor1@test.com
```

El comando crea o actualiza:

- `auth_user`
- `sellers_sellerprofile`
- `full_name`: `Vendedor de Prueba`
- `phone`: `00000000`
- `is_seller`: `true`
- `is_blocked`: `false`
- `is_active`: `true`

## Datos iniciales de sorteos

Despues de migrar:

```powershell
python manage.py seed_draws
```

Crea sorteos/horarios base:

- Manana: Diaria, Nica, Salvador. Cierre 11:00.
- Tarde: Diaria, Nica. Cierre 15:00.
- Noche: Diaria, Nica, Salvador, Bolido. Cierre 21:00.
- Sabado/Domingo: Santa. Cierre 15:00.
- Multiplicador por defecto: 72.

## Levantar servidor

```powershell
python manage.py runserver 0.0.0.0:8000
```

URLs utiles:

- Android emulador: `http://10.0.2.2:8000/`
- Navegador/local: `http://127.0.0.1:8000/`

## Endpoints iniciales

- `POST /api/auth/login/`
- `GET /api/auth/me/`
- `GET /api/draws/available/`
- `POST /api/sales/`
- `GET /api/sales/my-sales/`
- `GET /api/sales/{id}/`
- `GET /api/winners/my-winners/`

Todos excepto login requieren JWT:

```http
Authorization: Bearer <access_token>
```

## Login

Payload:

```json
{
  "username": "vendedor1",
  "password": "Vendedor123*"
}
```

Respuesta:

```json
{
  "success": true,
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "user": {
      "id": 1,
      "username": "vendedor1"
    }
  }
}
```

Prueba con PowerShell:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/auth/login/" `
  -ContentType "application/json" `
  -Body '{"username":"vendedor1","password":"Vendedor123*"}'

$token = $login.data.accessToken

Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/api/auth/me/" `
  -Headers @{ Authorization = "Bearer $token" }

Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/api/draws/available/" `
  -Headers @{ Authorization = "Bearer $token" }
```

Si el vendedor esta bloqueado:

```json
{
  "code": "USER_BLOCKED",
  "message": "Usuario bloqueado. Contacte al administrador."
}
```

## Registrar venta

Payload:

```json
{
  "buyer_name": "Juan Perez",
  "draw": 1,
  "draw_schedule": 1,
  "draw_date": "2026-06-27",
  "items": [
    { "number": "15", "amount": "10.00" },
    { "number": "22", "amount": "20.00" }
  ]
}
```

El backend calcula:

```txt
possible_prize = amount * payout_multiplier
```

Ejemplo con multiplicador 72:

- `1 * 1 = 72`
- `1 * 100 = 7200`

## Reglas implementadas

- El vendedor debe estar autenticado.
- El vendedor debe tener `SellerProfile`.
- Usuario bloqueado o inactivo recibe HTTP 403.
- Una venta requiere al menos un numero.
- No se permite vender si ya paso el cierre del sorteo.
- Se permiten sorteos futuros si no han cerrado.
- Un vendedor solo consulta sus propias ventas y ganadores.
- El premio posible se calcula en backend.

## Pendiente

- Endpoint administrativo para crear/cerrar sorteos desde Dashboard.
- Endpoint para ingresar resultados y calcular ganadores.
- Auditoria completa.
- Refresh/logout endpoints.
- Integracion de procedimientos almacenados MySQL.
- Notificaciones push.

## Compatibilidad Android Pendiente

La app Android actual espera algunos campos con nombres distintos a los serializers actuales de Django:

- Android `User` espera `name`, `role`, `isActive`, `isBlocked`; la API actual devuelve `first_name`, `last_name`, `is_active` y `seller`.
- Android `Draw` espera `category`, `drawDate`, `closeDateTime`, `status`, `payoutMultiplier`; la API actual devuelve `Draw` con lista `schedules`.
- Android `DrawSchedule` espera `drawId`, `label`, `closeTime`, `activeDays`; la API actual usa `event_name`, `close_time`, `days_of_week`.

Recomendacion para la siguiente fase: ajustar serializers Django para emitir camelCase compatible con Android, o agregar DTOs Android con `@SerializedName`.
