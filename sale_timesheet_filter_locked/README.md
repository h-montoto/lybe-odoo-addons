# Sale Timesheet - Filter Locked Orders

Módulo de Odoo 18 Community que filtra el selector de **Elemento de Pedido de Venta**
(`so_line`) en la aplicación de **Partes de Horas** para ocultar líneas pertenecientes
a pedidos en estado **bloqueado** (`done`) o **cancelado** (`cancel`).

## ¿Qué hace?

Hereda el modelo `account.analytic.line` y redefine el campo `so_line` añadiendo un
`domain` que excluye las líneas de venta cuyos pedidos están en estado `done` o
`cancel`. El resto del comportamiento del campo se conserva intacto.

## ¿Por qué existe?

En Odoo 18, cuando un comercial bloquea un pedido de venta (estado *done*), los
operarios siguen viendo sus líneas en el desplegable del parte de horas. Esto
genera confusión y, sobre todo, riesgo de imputar horas a pedidos ya cerrados
que no deberían admitir nuevos cargos.

Este módulo resuelve el problema en el origen: las líneas de pedidos bloqueados
o cancelados simplemente desaparecen del selector. Las horas ya imputadas se
mantienen sin alterar.

## Instalación

1. Copia la carpeta `sale_timesheet_filter_locked` dentro del directorio de
   addons personalizados de tu instancia de Odoo.
2. Reinicia el servicio de Odoo.
3. Activa el **Modo desarrollador**.
4. Ve a **Aplicaciones** → pulsa **Actualizar lista de aplicaciones**.
5. Busca `Sale Timesheet - Filter Locked Orders` e instálalo.

## Uso

El módulo es transparente: no añade menús ni vistas nuevas. Su efecto se observa
en el comportamiento del selector de pedido de venta en los partes de horas.

### Flujo típico

1. **Trabajar con normalidad**: imputas horas a líneas de un pedido de venta
   activo desde la aplicación de Partes de Horas.
2. **Bloquear el pedido**: cuando el responsable comercial pulsa *Bloquear* en
   un pedido de venta (estado pasa a `done`), las líneas de ese pedido
   desaparecen automáticamente del selector `so_line` en futuros partes.
3. **Necesitas añadir una línea nueva**: si por cualquier motivo hay que imputar
   más horas a un pedido bloqueado, desbloquéalo primero (volver a `sale`),
   añade la línea en el parte y vuelve a bloquearlo.
4. **Cancelar un pedido**: las líneas de pedidos en estado `cancel` también
   quedan ocultas con el mismo criterio.

> Importante: las imputaciones ya existentes no se borran ni se ocultan. Sólo se
> impide *crear* nuevas líneas de parte contra pedidos bloqueados o cancelados.

## Dependencias

- `sale_timesheet` (Odoo 18 Community)

## Licencia

LGPL-3
