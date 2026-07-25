# Procedimientos almacenados propuestos

Estos scripts se documentan dentro de `API DJANGO` porque en esta fase no se modifica `BASE DE DATOS MYSQL`.

## sp_create_sale

Responsabilidad:

- Validar que el vendedor exista, este activo y no bloqueado.
- Validar que el sorteo/horario no haya cerrado.
- Crear venta y detalle en una transaccion.
- Calcular `possible_prize = amount * payout_multiplier`.
- Devolver venta/recibo creado.

## sp_calculate_winners

Responsabilidad:

- Recibir sorteo, horario, fecha y numero ganador.
- Buscar `sale_items` con el numero ganador.
- Crear registros de ganadores.
- Calcular monto a pagar por vendedor.
- Evitar duplicados si el resultado ya fue procesado.

## sp_get_seller_summary

Responsabilidad:

- Resumir ventas por vendedor, fecha y sorteo.
- Total vendido.
- Total premios pendientes.
- Ganancia estimada.

## sp_get_profit_report

Responsabilidad:

- Comparar ingresos por sorteo contra premios a pagar.
- Agrupar por fecha, sorteo, horario y vendedor.
- Servir reportes del dashboard.

## sp_block_user

Responsabilidad:

- Bloquear usuario/vendedor.
- Registrar motivo, fecha y usuario administrador.
- Invalidar o marcar sesiones activas si se implementa tabla de sesiones.

## sp_audit_log

Responsabilidad:

- Registrar acciones criticas: login, venta, cierre de sorteo, ingreso de resultado, bloqueo y reimpresion.
