
============================
Factura electrónica española
============================

Módulo base para la creación de factura electrónica.

Permite configurar:

*Template para la generación del xml
*Schemas de validación del xml generado
*Estrategia de firma
*Estrategia del nombrado del xml generado
*Estrategia del envío del xml

Instalación
===========



Configuración
=============


Uso
===


Problemas conocidos / Hoja de ruta
==================================

* No está soportada la exportación de facturas rectificativas.
* Sólo se exportan IVAs repercutidos.
* No se controla el ancho de varios campos cuando se exportan.
* El certificado y la contraseña de acceso al certificado no se guardan
  cifrados en la base de datos.
* El fichero exportado debe subirse manualmente a la página de FACe. No está
  implementado el envío por servicio web, ya que tienen que conceder permiso
  expreso.
* Ver la posibilidad de exportar varias facturas juntas.
* Los apellidos de las personas físicas no se exportan.
* Soportar formato Factura-E v3.2.1.
