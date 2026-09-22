#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Always Free ARM64 Server Bootstrap Script
# Target: Ubuntu 24.04 LTS (aarch64 / ARM64 Ampere A1: 4 OCPU, 24 GB RAM)
# Cost: $0.00 / month forever
# ==============================================================================

set -euo pipefail

echo "===================================================================="
echo "  Deploying Gold Research Terminal on Oracle Always Free ARM64 VM  "
echo "===================================================================="

# 1. Update and install base utilities
echo "[1/6] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    curl \
    git \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    htop

# 2. Install Docker CE and Docker Compose plugin for ARM64
echo "[2/6] Installing Docker CE for ARM64..."
if ! command -v docker &> /dev/null; then
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker "$USER"
    echo "Docker installed successfully."
fi

# 3. Install Tailscale for Zero-Trust Private Access
echo "[3/6] Installing Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo systemctl enable --now tailscaled
    echo "Tailscale installed. Run 'sudo tailscale up' to authenticate this node."
fi

# 4. Configure Firewall (UFW) - Block public DB/API, allow Tailscale & SSH
echo "[4/6] Hardening Firewall (UFW)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
# Allow tailscale interface traffic
sudo ufw allow in on tailscale0
# Enable firewall non-interactively
sudo ufw --force enable

# 5. Build and Launch Docker Compose Stack
echo "[5/6] Launching Gold Research Terminal Stack..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ ! -f .env ]; then
    echo "Creating production .env from default template..."
    cat <<EOF > .env
APP_ENV=production
DB_PASSWORD=$(openssl rand -hex 16)
DATABASE_URL=postgresql://gold_quant:gold_quant_secure_2026@postgres:5432/gold_research
EOF
fi

# Build and start services
docker compose -f deploy/docker-compose.yml up -d --build

# 6. Verify stack health
echo "[6/6] Verifying system health..."
sleep 10
docker compose -f deploy/docker-compose.yml ps

echo "===================================================================="
echo "  DEPLOYMENT COMPLETE!                                              "
echo "  Terminal UI running on: http://localhost:3000                     "
echo "  Tailscale private URL:  http://<tailscale-ip>:3000                "
echo "  PostgreSQL & API are isolated inside internal Docker network.     "
echo "===================================================================="
