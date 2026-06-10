#!/usr/bin/env bash
#
# freqtrade-ve.sh — Proxmox VE helper to spin up an LXC and install freqtrade.
#
# Run this ON THE PROXMOX HOST (not inside a container):
#     bash -c "$(curl -fsSL <raw-url>/proxmox/freqtrade-ve.sh)"
#   or
#     ./proxmox/freqtrade-ve.sh
#
# Choices:
#   - Source repo:  your fork (cyberjunky/improvements, blofin) OR stock (freqtrade/develop)
#   - user_data:    bind-mounted from the PVE host so it survives CT rebuild/destroy
#   - SSH:          optional root password + sshd so you can VS Code Remote-SSH / SFTP in
#
# Non-interactive overrides (export before running to skip prompts):
#   CTID HOSTNAME DISK CORES RAM SWAP BRIDGE STORAGE TEMPLATE_STORAGE
#   REPO_CHOICE(fork|dev) ENABLE_SSH(yes|no) ROOT_PW DATA_ROOT
#
set -euo pipefail

# ---- defaults -------------------------------------------------------------
HOSTNAME="${HOSTNAME:-freqtrade-prod}"
DISK="${DISK:-16}"                # GB
CORES="${CORES:-4}"
RAM="${RAM:-4096}"                # MB
SWAP="${SWAP:-1024}"              # MB
BRIDGE="${BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"           # rootfs storage
# template storage: auto-pick the first storage that supports CT templates (vztmpl)
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-$(pvesm status -content vztmpl 2>/dev/null | awk 'NR>1{print $1; exit}')}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"  # fallback
DATA_ROOT="${DATA_ROOT:-/opt/ft-data}"    # host dir holding each CT's user_data
CT_DIR="/opt/freqtrade"                   # install dir inside the container
TEMPLATE_NAME="debian-13-standard"        # Debian 13 trixie, Python 3.13 (freqtrade needs >=3.11)
UNPRIV_ROOT_UID=100000                    # uid that CT-root maps to on the host

FORK_URL="https://github.com/cyberjunky/freqtrade.git";  FORK_BRANCH="improvements"
DEV_URL="https://github.com/freqtrade/freqtrade.git";    DEV_BRANCH="develop"

msg()  { echo -e "\e[1;32m[+]\e[0m $*"; }
warn() { echo -e "\e[1;33m[!]\e[0m $*"; }
die()  { echo -e "\e[1;31m[x]\e[0m $*" >&2; exit 1; }

# ---- sanity ---------------------------------------------------------------
command -v pct >/dev/null   || die "pct not found — run this on the Proxmox VE host."
command -v pveam >/dev/null || die "pveam not found — run this on the Proxmox VE host."
[ "$(id -u)" -eq 0 ]        || die "Run as root on the PVE host."

CTID="${CTID:-$(pvesh get /cluster/nextid)}"

# ---- prompts (whiptail if interactive) ------------------------------------
if [ -t 0 ] && command -v whiptail >/dev/null; then
  REPO_CHOICE="${REPO_CHOICE:-$(whiptail --title "freqtrade source" --menu \
    "Which repo to install into CT $CTID?" 12 70 2 \
    "fork" "cyberjunky/improvements  (blofin + your changes)" \
    "dev"  "freqtrade/develop        (stock latest)" \
    3>&1 1>&2 2>&3)}" || die "cancelled"

  if whiptail --title "SSH access" --yesno \
       "Enable sshd + set a root password?\n(needed for VS Code Remote-SSH / SFTP)" 10 60; then
    ENABLE_SSH="yes"
    ROOT_PW="${ROOT_PW:-$(whiptail --title "root password" --passwordbox \
      "Root password for CT $CTID:" 9 60 3>&1 1>&2 2>&3)}" || die "cancelled"
  else
    ENABLE_SSH="no"
  fi
else
  REPO_CHOICE="${REPO_CHOICE:-fork}"
  ENABLE_SSH="${ENABLE_SSH:-yes}"
fi

case "$REPO_CHOICE" in
  fork) REPO_URL="$FORK_URL"; BRANCH="$FORK_BRANCH" ;;
  dev)  REPO_URL="$DEV_URL";  BRANCH="$DEV_BRANCH"  ;;
  *) die "REPO_CHOICE must be 'fork' or 'dev'" ;;
esac
ENABLE_SSH="${ENABLE_SSH:-yes}"

# ---- template -------------------------------------------------------------
if ! pvesm status -content vztmpl 2>/dev/null | awk 'NR>1{print $1}' | grep -qx "$TEMPLATE_STORAGE"; then
  die "Storage '$TEMPLATE_STORAGE' does not allow CT templates (vztmpl).
     Enable it:   pvesm set $TEMPLATE_STORAGE --content iso,vztmpl,backup,snippets
     Or point at another storage:  TEMPLATE_STORAGE=<name> $0"
fi
msg "Ensuring $TEMPLATE_NAME template is present (storage: $TEMPLATE_STORAGE)..."
pveam update >/dev/null 2>&1 || true
TEMPLATE_FILE="$(pveam available --section system | awk -v n="$TEMPLATE_NAME" '$2 ~ n {print $2}' | sort | tail -n1)"
[ -n "$TEMPLATE_FILE" ] || die "No $TEMPLATE_NAME template available via pveam."
if ! pveam list "$TEMPLATE_STORAGE" 2>/dev/null | grep -q "$TEMPLATE_FILE"; then
  msg "Downloading $TEMPLATE_FILE to $TEMPLATE_STORAGE..."
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE_FILE"
fi
TEMPLATE_REF="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_FILE}"

# ---- host data dir (bind mount target) ------------------------------------
HOST_DATA="${DATA_ROOT%/}/${CTID}"
msg "Preparing host data dir $HOST_DATA (survives CT rebuild)..."
mkdir -p "$HOST_DATA"
# unprivileged CT: CT-root (uid 0) maps to host uid 100000 — own the bind dir to it
chown -R "${UNPRIV_ROOT_UID}:${UNPRIV_ROOT_UID}" "$HOST_DATA"

# ---- create the container -------------------------------------------------
msg "Creating LXC $CTID ($HOSTNAME)..."
pct create "$CTID" "$TEMPLATE_REF" \
  --hostname "$HOSTNAME" \
  --cores "$CORES" --memory "$RAM" --swap "$SWAP" \
  --rootfs "${STORAGE}:${DISK}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
  --unprivileged 1 --features nesting=1 --onboot 1

# bind-mount host user_data into the CT
pct set "$CTID" -mp0 "${HOST_DATA},mp=${CT_DIR}/user_data"

msg "Starting CT $CTID..."
pct start "$CTID"

# wait for network/DNS inside the CT
msg "Waiting for network..."
for _ in $(seq 1 30); do
  pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1 && break
  sleep 2
done

# ---- generate the in-container installer ----------------------------------
INSTALLER="$(mktemp)"
cat >"$INSTALLER" <<INSTALL
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
REPO_URL="$REPO_URL"; BRANCH="$BRANCH"; CT_DIR="$CT_DIR"
ENABLE_SSH="$ENABLE_SSH"; ROOT_PW="${ROOT_PW:-}"

echo "[ct] full upgrade (latest security patches)..."
apt-get update -qq
apt-get -y -qq dist-upgrade >/dev/null

echo "[ct] apt deps..."
apt-get install -y -qq git curl ca-certificates \\
  python3 python3-venv python3-dev \\
  build-essential libssl-dev libffi-dev pkg-config cmake gcc \\
  sqlite3 libgomp1 libatlas3-base libgfortran5 >/dev/null

echo "[ct] enable automatic security updates..."
apt-get install -y -qq unattended-upgrades >/dev/null
printf 'APT::Periodic::Update-Package-Lists "1";\\nAPT::Periodic::Unattended-Upgrade "1";\\n' \\
  >/etc/apt/apt.conf.d/20auto-upgrades
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true

echo "[ct] clone \$REPO_URL (\$BRANCH)..."
# /opt/freqtrade already exists (user_data is bind-mounted under it), so clone
# elsewhere and copy the repo in alongside the mounted user_data.
rm -rf /tmp/ftsrc
git clone --depth 1 -b "\$BRANCH" "\$REPO_URL" /tmp/ftsrc
mkdir -p "\$CT_DIR"
cp -a /tmp/ftsrc/. "\$CT_DIR"/
rm -rf /tmp/ftsrc

echo "[ct] venv + install (ta-lib 0.6.x ships bundled wheels, no C build)..."
python3 -m venv "\$CT_DIR/.venv"
"\$CT_DIR/.venv/bin/pip" install -q --upgrade pip wheel setuptools
"\$CT_DIR/.venv/bin/pip" install -q -e "\$CT_DIR"

echo "[ct] init user_data (into bind-mounted host dir) + freqUI..."
"\$CT_DIR/.venv/bin/freqtrade" create-userdir --userdir "\$CT_DIR/user_data" || true
"\$CT_DIR/.venv/bin/freqtrade" install-ui || true

echo "[ct] systemd TEMPLATE unit (one instance per bot)..."
# Usage: systemctl enable --now freqtrade@<name>
#   -> config user_data/<name>.json, private DB user_data/<name>.sqlite
cat >/etc/systemd/system/freqtrade@.service <<UNIT
[Unit]
Description=freqtrade bot %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=\$CT_DIR
ExecStart=\$CT_DIR/.venv/bin/freqtrade trade \\
  --config \$CT_DIR/user_data/%i.json \\
  --userdir \$CT_DIR/user_data \\
  --db-url sqlite:///\$CT_DIR/user_data/%i.sqlite \\
  --logfile \$CT_DIR/user_data/logs/%i.log
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload

if [ "\$ENABLE_SSH" = "yes" ]; then
  echo "[ct] sshd for VS Code Remote-SSH / SFTP..."
  apt-get install -y -qq openssh-server >/dev/null
  sed -i 's/^#\\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  sed -i 's/^#\\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
  systemctl enable --now ssh >/dev/null 2>&1 || systemctl enable --now sshd >/dev/null 2>&1 || true
  [ -n "\$ROOT_PW" ] && echo "root:\$ROOT_PW" | chpasswd

  # generate a fresh root key on first run (idempotent) and authorize it
  KEY=/root/.ssh/ft_ed25519
  mkdir -p /root/.ssh && chmod 700 /root/.ssh
  if [ ! -f "\$KEY" ]; then
    ssh-keygen -t ed25519 -N "" -C "freqtrade-ct" -f "\$KEY" >/dev/null
    cat "\$KEY.pub" >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
  fi
fi

echo "[ct] done."
INSTALL

msg "Running installer inside CT $CTID..."
pct push "$CTID" "$INSTALLER" /root/ft-install.sh
pct exec "$CTID" -- bash /root/ft-install.sh
rm -f "$INSTALLER"

# ---- summary --------------------------------------------------------------
IP="$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}')"
echo
msg "freqtrade installed in CT $CTID."
echo "  repo        : $REPO_URL ($BRANCH)"
echo "  install dir : $CT_DIR  (in CT)"
echo "  user_data   : $HOST_DATA  (on HOST) -> $CT_DIR/user_data (in CT)"
echo "  IP          : ${IP:-<dhcp pending>}"
echo
echo "Multiple bots — one systemd instance per config (freqtrade@<name>):"
echo "  1) per bot, drop ${HOST_DATA}/<name>.json (unique bot_name + api_server.listen_port)"
echo "     generate: pct exec $CTID -- $CT_DIR/.venv/bin/freqtrade new-config --config $CT_DIR/user_data/<name>.json"
echo "     DB + logfile are auto per-instance: user_data/<name>.sqlite, logs/<name>.log"
echo "  2) pct exec $CTID -- systemctl enable --now freqtrade@<name>"
echo "  3) status/logs: pct exec $CTID -- systemctl status 'freqtrade@*'"
echo "                  pct exec $CTID -- journalctl -u freqtrade@<name> -f"

if [ "$ENABLE_SSH" = "yes" ]; then
  KEY_OUT="${HOST_DATA%/}/../${CTID}_id_ed25519"
  pct exec "$CTID" -- cat /root/.ssh/ft_ed25519 > "$KEY_OUT" 2>/dev/null && chmod 600 "$KEY_OUT"
  echo
  echo "SSH (key-based) for VS Code Remote-SSH / SFTP:"
  echo "  ssh -i <key> root@${IP:-<ip>}    (open folder $CT_DIR)"
  echo "  private key saved on this host: $KEY_OUT"
  echo "  --- copy this private key to your client (~/.ssh) ----------------------"
  pct exec "$CTID" -- cat /root/.ssh/ft_ed25519
  echo "  -----------------------------------------------------------------------"
fi
echo
echo "Update later:  pct exec $CTID -- bash -lc 'cd $CT_DIR && git pull && .venv/bin/pip install -e .'"
echo "               pct exec $CTID -- systemctl restart 'freqtrade@*'"
