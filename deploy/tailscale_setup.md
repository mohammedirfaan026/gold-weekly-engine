# Tailscale Private Network Architecture for Gold Research Terminal

## Overview

The Gold Research Terminal is designed to run in a **Zero-Trust Private Mesh Network**. Neither PostgreSQL (port 5432) nor the internal FastAPI backend (port 8000) or Caddy are exposed to the open internet.

Access is mediated entirely through **Tailscale** (encrypted WireGuard overlay network).

```
+----------------------------------------------------------------+
|                        TAILSCALE MESH                          |
|                                                                |
|   +--------------------+               +-------------------+   |
|   |  Your Laptop/Phone | <-----------> |  Oracle Cloud VM  |   |
|   |  100.x.y.z         |  (Encrypted)  |  100.a.b.c        |   |
|   +--------------------+               +---------+---------+   |
+--------------------------------------------------|-------------+
                                                   | (Internal Docker Network)
                                       +-----------+------------+
                                       |                        |
                                 +-----+------+           +-----+------+
                                 |  Frontend  |           |  Postgres  |
                                 |  (Next.js) |           |  (PG 16)   |
                                 +-----+------+           +------------+
                                       |
                                 +-----+------+
                                 |  FastAPI   |
                                 |  Backend   |
                                 +------------+
```

---

## Step 1: Connect Oracle Cloud VM to Tailscale

SSH into your Oracle Cloud VM:

```bash
ssh ubuntu@<your-oracle-public-ip>
```

Run Tailscale authentication:

```bash
sudo tailscale up --ssh --operator=ubuntu
```

Click the login link generated in the terminal to authenticate the VM to your Tailscale account.

Once authenticated, verify your private Tailscale IP:

```bash
tailscale ip -4
# Example output: 100.85.120.45
```

---

## Step 2: Lock Down Oracle Cloud Security Lists & Firewall

In the Oracle Cloud Console:
1. Navigate to **Networking > Virtual Cloud Networks > Your VCN > Security Lists**.
2. Restrict Ingress Rules:
   - **Port 22 (SSH)**: You can leave open or allow only from your home IP.
   - **Ports 80, 443, 3000, 5432, 8000**: **DO NOT ADD INGRESS RULES FOR THESE PORTS** in the Oracle Cloud Public Security List.

On the VM:
```bash
# Allow traffic on the Tailscale virtual interface
sudo ufw allow in on tailscale0

# Enable firewall
sudo ufw enable
```

---

## Step 3: Accessing the Research Terminal

From any of your authorized devices (laptop, phone, tablet) connected to Tailscale:

Open your browser and navigate to:

```
http://<oracle-tailscale-ip>:3000
```
Or using MagicDNS (e.g. `http://gold-research-terminal:3000`).

---

## Step 4: Maintenance & Direct Database Access

To inspect PostgreSQL directly using DBeaver, TablePlus, or psql through Tailscale:

SSH port forwarding over Tailscale:
```bash
ssh -L 5432:localhost:5432 ubuntu@<oracle-tailscale-ip>
```
Or connect directly over the Tailscale IP if port 5432 is bound to `100.x.y.z`.
