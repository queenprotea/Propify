# Acceso a Propify desde otros equipos de la red local (LAN)

Propify puede usarse desde cualquier dispositivo (otra PC, laptop, teléfono o
tableta) conectado a la **misma red local** que el servidor donde se ejecuta.

## ¿Cómo funciona?

El navegador del cliente **solo se comunica con el frontend** (puerto `3000`).
El frontend (nginx) reenvía internamente las llamadas `/api/...` al *API Gateway*,
que a su vez habla con los microservicios por la red interna de Docker.
Por eso **no hay problemas de CORS** ni hace falta exponer cada microservicio:
basta con que el puerto del frontend sea accesible desde la LAN.

```
[Dispositivo LAN] --:3000--> [frontend nginx] --/api--> [gateway] --> [user/property/contract/payment]
```

## 1. Obtener la IP local del servidor

- **macOS:**   `ipconfig getifaddr en0`
- **Linux:**   `hostname -I | awk '{print $1}'`
- **Windows:** `ipconfig` → "Dirección IPv4" del adaptador activo

> En este servidor la IP local es, por ejemplo: **192.168.1.65**

## 2. URL a usar desde otros equipos

```
http://<IP_LOCAL_DEL_SERVIDOR>:3000
```

Ejemplo: **http://192.168.1.65:3000**

Usuario administrador inicial: `admin@propify.com` / `Admin1234`.

---

## Producción / despliegue con Docker (recomendado)

Los puertos ya se publican en **todas las interfaces** (`0.0.0.0`), por lo que el
acceso desde la LAN funciona sin cambios:

```bash
cd backend
docker compose up -d --build
```

Quedan accesibles desde la red:
- **Frontend (la app):** `http://<IP_LOCAL>:3000`
- **API Gateway (opcional):** `http://<IP_LOCAL>:8080`

Los microservicios (`8001`, `8002`, `8003`, `8000`) están enlazados a `127.0.0.1`
**a propósito**: no se exponen a la red; el único punto de entrada es el gateway.
La base de datos (`5432`) también está restringida a loopback.

## Desarrollo (Vite + backend en Docker)

1. Levanta el backend (incluye el gateway en `:8080`):
   ```bash
   cd backend && docker compose up -d
   ```
2. Arranca el frontend en modo desarrollo (ya configurado para escuchar en `0.0.0.0`):
   ```bash
   cd frontend && npm install && npm run dev
   ```
   Acceso desde la LAN: **http://<IP_LOCAL>:5173**

   > El proxy de Vita reenvía `/api` a `http://localhost:8080` **en el servidor**,
   > así que las llamadas de los clientes LAN también funcionan (el proxy es del lado servidor).
   > Si el gateway corriera en otra máquina, define `VITE_API_TARGET` al arrancar:
   > `VITE_API_TARGET=http://otra-ip:8080 npm run dev`

3. Vista previa del build de producción (sirve `dist/` en `:4173`, también en la LAN):
   ```bash
   npm run build && npm run preview
   ```

---

## 3. Firewall

El acceso por la LAN requiere que el puerto del frontend (`3000`, o `5173` en dev)
no esté bloqueado por el firewall del servidor.

- **macOS:** En este equipo el firewall está **desactivado** (sin restricciones).
  Si lo activas (Ajustes → Red → Firewall), permite conexiones entrantes para
  *Docker Desktop* (o `node` en desarrollo). Verificar estado:
  ```bash
  /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
  ```
- **Linux (ufw):**
  ```bash
  sudo ufw allow 3000/tcp
  sudo ufw allow 8080/tcp   # opcional, solo si se accede al gateway directo
  ```
- **Windows:** Panel de control → Firewall de Windows Defender → "Permitir una
  aplicación" → habilita Docker Desktop / Node, o crea una regla de entrada para
  el puerto TCP 3000.

## 4. Comprobación rápida

Desde otro equipo de la red (sustituye la IP):

```bash
curl http://192.168.1.65:3000/                 # debe responder HTML (200)
curl http://192.168.1.65:3000/api/users/health # {"status":"ok"}
```

O simplemente abre `http://192.168.1.65:3000` en el navegador del otro dispositivo.

## Notas

- Las IPs `192.168.x.x` / `10.x.x.x` son privadas: el acceso funciona dentro de la
  misma red. Para acceso desde Internet se necesitaría reenvío de puertos o un
  túnel/HTTPS, fuera del alcance de la red local.
- La IP local puede cambiar si el router la asigna por DHCP; conviene reservarla.
