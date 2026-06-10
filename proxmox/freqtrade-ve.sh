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
#   - Storage:      pick which pool holds the CT disk (shows usage)
#   - user_data:    kept INSIDE the container (on its disk), persisted via a
#                   scheduled Proxmox vzdump backup job of the whole CT
#   - SSH login:    a sudo user (recommended) or root; key generated + displayed
#   - venv:         freqtrade installs into a .venv in the run user's home dir,
#                   and the bot runs as that (non-root) user.
#
# Non-interactive overrides (export before running to skip prompts):
#   CTID CT_HOSTNAME DISK CORES RAM SWAP BRIDGE STORAGE TEMPLATE_STORAGE
#   REPO_CHOICE(fork|dev) ENABLE_SSH(yes|no) SSH_USER (""=root-only) SSH_USER_PW ROOT_PW
#   ENABLE_BACKUP(yes|no) BACKUP_STORAGE BACKUP_SCHEDULE(e.g. "03:00") BACKUP_KEEP(int)
#   KEY_DIR (host dir to save the generated private key)
#
set -euo pipefail

# ---- defaults -------------------------------------------------------------
# NB: do NOT name this HOSTNAME — the PVE host shell exports HOSTNAME=pve,
# which would override the default and name every CT "pve".
CT_HOSTNAME="${CT_HOSTNAME:-freqtrade-prod}"
DISK="${DISK:-20}"                # GB (data lives inside the CT, so give it room)
CORES="${CORES:-4}"
RAM="${RAM:-4096}"                # MB
SWAP="${SWAP:-1024}"              # MB
BRIDGE="${BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-}"                     # rootfs storage (prompted; falls back to local-lvm)
# template storage: auto-pick the first storage that supports CT templates (vztmpl)
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-$(pvesm status -content vztmpl 2>/dev/null | awk 'NR>1{print $1; exit}')}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"  # fallback
KEY_DIR="${KEY_DIR:-/root/freqtrade-ct-keys}"  # host dir to stash the generated SSH key
# CT_DIR / VENV are derived from the run user's home below (so the workspace shows them)
TEMPLATE_NAME="debian-13-standard"        # Debian 13 trixie, Python 3.13 (freqtrade needs >=3.11)

# backups: schedule a vzdump of the whole CT so in-container data is recoverable
ENABLE_BACKUP="${ENABLE_BACKUP:-yes}"
BACKUP_STORAGE="${BACKUP_STORAGE:-}"      # backup-capable storage (prompted; auto if blank)
BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-03:00}"
BACKUP_KEEP="${BACKUP_KEEP:-7}"

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

  # rootfs storage — choose among storages that can hold a CT disk (content rootdir),
  # showing usage so you can avoid a full pool.
  _st_items=()
  while read -r _n _t _u; do _st_items+=("$_n" "$_t  (${_u} used)"); done \
    < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1{print $1, $2, $7}')
  if [ "${#_st_items[@]}" -ge 2 ]; then
    STORAGE="${STORAGE:-$(whiptail --title "rootfs storage" --menu \
      "Where should the CT disk (rootfs) live?" 16 64 6 \
      "${_st_items[@]}" 3>&1 1>&2 2>&3)}" || die "cancelled"
  fi

  if whiptail --title "SSH access" --yesno \
       "Enable sshd for VS Code Remote-SSH / SFTP?" 9 60; then
    ENABLE_SSH="yes"
    SSH_MODE="$(whiptail --title "SSH login" --menu \
      "How do you want to log in?" 12 64 2 \
      "user" "create a sudo user (recommended)" \
      "root" "log in as root directly" \
      3>&1 1>&2 2>&3)" || die "cancelled"
    if [ "$SSH_MODE" = "user" ]; then
      SSH_USER="${SSH_USER:-$(whiptail --title "username" --inputbox \
        "Login username (added to sudo group, runs the bot):" 9 60 "ft" 3>&1 1>&2 2>&3)}" || die "cancelled"
      SSH_USER_PW="${SSH_USER_PW:-$(whiptail --title "password" --passwordbox \
        "Password for '${SSH_USER}'  (blank = key-only login):" 9 60 3>&1 1>&2 2>&3)}" || die "cancelled"
    else
      SSH_USER=""
      ROOT_PW="${ROOT_PW:-$(whiptail --title "root password" --passwordbox \
        "Root password  (blank = key-only login):" 9 60 3>&1 1>&2 2>&3)}" || die "cancelled"
    fi
  else
    ENABLE_SSH="no"
  fi

  # backups — schedule a vzdump of the whole CT (so in-container data survives)
  if whiptail --title "Backups" --yesno \
       "Schedule a daily backup of this CT?\n(vzdump of the whole container — data + config)" 10 60; then
    ENABLE_BACKUP="yes"
    _bk_items=()
    while read -r _n _t _u; do _bk_items+=("$_n" "$_t  (${_u} used)"); done \
      < <(pvesm status -content backup 2>/dev/null | awk 'NR>1{print $1, $2, $7}')
    if [ "${#_bk_items[@]}" -ge 2 ]; then
      BACKUP_STORAGE="${BACKUP_STORAGE:-$(whiptail --title "backup storage" --menu \
        "Where should backups be stored?" 16 64 6 \
        "${_bk_items[@]}" 3>&1 1>&2 2>&3)}" || die "cancelled"
    fi
  else
    ENABLE_BACKUP="no"
  fi
else
  REPO_CHOICE="${REPO_CHOICE:-fork}"
fi

case "$REPO_CHOICE" in
  fork) REPO_URL="$FORK_URL"; BRANCH="$FORK_BRANCH" ;;
  dev)  REPO_URL="$DEV_URL";  BRANCH="$DEV_BRANCH"  ;;
  *) die "REPO_CHOICE must be 'fork' or 'dev'" ;;
esac

# normalize (set -u safe). SSH_USER="" (explicitly) => root-only; unset => 'ft'.
ENABLE_SSH="${ENABLE_SSH:-yes}"
STORAGE="${STORAGE:-local-lvm}"    # fallback if not picked / non-interactive
SSH_USER="${SSH_USER-ft}"
SSH_USER_PW="${SSH_USER_PW:-}"
ROOT_PW="${ROOT_PW:-}"
ENABLE_BACKUP="${ENABLE_BACKUP:-yes}"
# auto-pick a backup-capable storage if one wasn't chosen
if [ "$ENABLE_BACKUP" = "yes" ] && [ -z "$BACKUP_STORAGE" ]; then
  BACKUP_STORAGE="$(pvesm status -content backup 2>/dev/null | awk 'NR>1{print $1; exit}')"
fi

# run user + paths. Install freqtrade UNDER the run user's home so the code AND
# user_data show up in the VS Code remote workspace; venv stays in the freqtrade
# dir (freqtrade's own .venv convention), i.e. inside the user's home tree.
if [ -n "$SSH_USER" ]; then RUN_USER="$SSH_USER"; RUN_HOME="/home/$SSH_USER"
else RUN_USER="root"; RUN_HOME="/root"; fi
CT_DIR="$RUN_HOME/freqtrade"          # ~/freqtrade  -> user_data at ~/freqtrade/user_data
VENV="$CT_DIR/.venv"

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

# ---- create the container -------------------------------------------------
# Data lives INSIDE the CT (no bind-mount); it's persisted by the backup job below.
msg "Creating LXC $CTID ($CT_HOSTNAME) on $STORAGE (${DISK}G)..."
pct create "$CTID" "$TEMPLATE_REF" \
  --hostname "$CT_HOSTNAME" \
  --cores "$CORES" --memory "$RAM" --swap "$SWAP" \
  --rootfs "${STORAGE}:${DISK}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
  --unprivileged 1 --features nesting=1 --onboot 1

msg "Starting CT $CTID..."
pct start "$CTID"

# wait for network/DNS inside the CT
msg "Waiting for network..."
for _ in $(seq 1 30); do
  pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1 && break
  sleep 2
done

# ---- generate the in-container installer ----------------------------------
# Quoted heredoc => nothing expands on the PVE host; the actual values are
# injected as a small preamble of shell assignments, so the body uses plain
# $VARs (no escaping). NOTE: passwords containing a single quote would break the
# preamble quoting — avoid those.
INSTALLER="$(mktemp)"
{
cat <<PREAMBLE
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8 LC_ALL=C.UTF-8
REPO_URL='$REPO_URL'
BRANCH='$BRANCH'
CT_DIR='$CT_DIR'
ENABLE_SSH='$ENABLE_SSH'
ROOT_PW='$ROOT_PW'
SSH_USER='$SSH_USER'
SSH_USER_PW='$SSH_USER_PW'
RUN_USER='$RUN_USER'
VENV='$VENV'
PREAMBLE
cat <<'INSTALL'

echo "[ct] full upgrade (latest security patches)..."
apt-get update -qq
apt-get -y -qq dist-upgrade >/dev/null

echo "[ct] apt deps..."
apt-get install -y -qq git curl ca-certificates sudo \
  python3 python3-venv python3-dev \
  build-essential libssl-dev libffi-dev pkg-config cmake gcc \
  sqlite3 libgomp1 libatlas3-base libgfortran5 >/dev/null

# Generate en_US.UTF-8 so SSH clients (VS Code) forwarding LANG=en_US.UTF-8
# don't spew "cannot change locale" warnings in every shell.
localedef -i en_US -f UTF-8 en_US.UTF-8 >/dev/null 2>&1 || true

echo "[ct] automatic security updates..."
apt-get install -y -qq unattended-upgrades >/dev/null
printf 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";\n' \
  >/etc/apt/apt.conf.d/20auto-upgrades
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true

# ── login account: a sudo user (default) or root ────────────────────────────
if [ -n "$SSH_USER" ]; then
  id "$SSH_USER" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "$SSH_USER"
  usermod -aG sudo "$SSH_USER"
  [ -n "$SSH_USER_PW" ] && echo "$SSH_USER:$SSH_USER_PW" | chpasswd
  # key-only login (no password) => grant passwordless sudo so the user isn't
  # locked out of sudo; with a password set, normal (password) sudo applies.
  if [ -z "$SSH_USER_PW" ]; then
    echo "$SSH_USER ALL=(ALL) NOPASSWD:ALL" >"/etc/sudoers.d/90-ft-$SSH_USER"
    chmod 440 "/etc/sudoers.d/90-ft-$SSH_USER"
  fi
fi

# run a command as the run user (or directly if root)
run() { if [ "$RUN_USER" = root ]; then bash -lc "$1"; else runuser -u "$RUN_USER" -- bash -lc "$1"; fi; }

echo "[ct] clone $REPO_URL ($BRANCH) -> $CT_DIR ..."
# clone to a temp dir then copy in (keeps $CT_DIR setup simple).
rm -rf /tmp/ftsrc
git clone --depth 1 -b "$BRANCH" "$REPO_URL" /tmp/ftsrc
mkdir -p "$CT_DIR"
cp -a /tmp/ftsrc/. "$CT_DIR"/
rm -rf /tmp/ftsrc
# own the whole tree (incl. the empty user_data mount) by the run user so the bot
# can read code and write data; on an unprivileged CT this maps through the
# bind-mount to the host (uid 100000+1000) automatically.
chown -R "$RUN_USER:$RUN_USER" "$CT_DIR"

echo "[ct] venv + install in $VENV (run user's home; ta-lib 0.6.x ships wheels)..."
run "python3 -m venv '$VENV'"
run "'$VENV/bin/pip' install -q --upgrade pip wheel setuptools"
run "'$VENV/bin/pip' install -q -e '$CT_DIR'"

echo "[ct] init user_data + freqUI (as $RUN_USER)..."
run "'$VENV/bin/freqtrade' create-userdir --userdir '$CT_DIR/user_data'" || true
run "'$VENV/bin/freqtrade' install-ui" || true

echo "[ct] systemd template unit (one instance per bot, runs as $RUN_USER)..."
# Usage: systemctl enable --now freqtrade@<name>
#   -> config user_data/<name>.json, private DB user_data/<name>.sqlite
cat >/etc/systemd/system/freqtrade@.service <<UNIT
[Unit]
Description=freqtrade bot %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$CT_DIR
ExecStart=$VENV/bin/freqtrade trade --config $CT_DIR/user_data/%i.json --userdir $CT_DIR/user_data --db-url sqlite:///$CT_DIR/user_data/%i.sqlite --logfile $CT_DIR/user_data/logs/%i.log
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload

if [ "$ENABLE_SSH" = yes ]; then
  echo "[ct] sshd (VS Code Remote-SSH / SFTP)..."
  apt-get install -y -qq openssh-server >/dev/null
  # sshd uses the FIRST value seen for each keyword, and Debian Includes
  # sshd_config.d/*.conf (alphabetical) at the top — so to override any other
  # drop-in (e.g. a cloud/template one setting PasswordAuthentication no) ours
  # must sort FIRST. Hence 00-ft.conf, not 99-.
  if [ -n "$SSH_USER" ]; then prl=prohibit-password; else prl=yes; fi
  cat >/etc/ssh/sshd_config.d/00-ft.conf <<SSHD
PermitRootLogin $prl
PasswordAuthentication yes
PubkeyAuthentication yes
SSHD

  # one ed25519 keypair, authorized for whichever account(s) you log in as
  KEY=/root/.ssh/ft_ed25519
  mkdir -p /root/.ssh && chmod 700 /root/.ssh
  [ -f "$KEY" ] || ssh-keygen -t ed25519 -N "" -C freqtrade-ct -f "$KEY" >/dev/null
  PUB="$(cat "$KEY.pub")"
  authorize() {  # $1=home  $2=user:group
    install -d -m700 -o "${2%%:*}" -g "${2##*:}" "$1/.ssh"
    grep -qxF "$PUB" "$1/.ssh/authorized_keys" 2>/dev/null || echo "$PUB" >> "$1/.ssh/authorized_keys"
    chmod 600 "$1/.ssh/authorized_keys"; chown "$2" "$1/.ssh/authorized_keys"
  }
  authorize /root root:root
  [ -n "$ROOT_PW" ] && echo "root:$ROOT_PW" | chpasswd
  [ -n "$SSH_USER" ] && authorize "/home/$SSH_USER" "$SSH_USER:$SSH_USER"
  systemctl enable ssh >/dev/null 2>&1 || systemctl enable sshd >/dev/null 2>&1 || true
  systemctl restart ssh >/dev/null 2>&1 || systemctl restart sshd >/dev/null 2>&1 || true
fi

echo "[ct] done."
INSTALL
} >"$INSTALLER"

msg "Running installer inside CT $CTID..."
pct push "$CTID" "$INSTALLER" /root/ft-install.sh
pct exec "$CTID" -- bash /root/ft-install.sh
rm -f "$INSTALLER"

# ---- scheduled backup (persists the in-container data) --------------------
BACKUP_INFO="(disabled)"
if [ "$ENABLE_BACKUP" = "yes" ] && [ -n "$BACKUP_STORAGE" ]; then
  msg "Creating daily backup job: $BACKUP_STORAGE @ $BACKUP_SCHEDULE, keep $BACKUP_KEEP..."
  if pvesh create /cluster/backup \
       --vmid "$CTID" --storage "$BACKUP_STORAGE" --schedule "$BACKUP_SCHEDULE" \
       --mode snapshot --compress zstd --prune-backups "keep-last=$BACKUP_KEEP" \
       --enabled 1 --comment "freqtrade CT $CTID" >/dev/null 2>&1; then
    BACKUP_INFO="$BACKUP_STORAGE daily @ $BACKUP_SCHEDULE (keep $BACKUP_KEEP)"
  else
    warn "Backup job creation failed (storage '$BACKUP_STORAGE' backup-capable? snapshot supported?)."
    warn "Set one up later: Datacenter > Backup > Add, or: pvesh create /cluster/backup --vmid $CTID --storage <s> --schedule '$BACKUP_SCHEDULE' --mode snapshot"
    BACKUP_INFO="(failed — configure manually)"
  fi
elif [ "$ENABLE_BACKUP" = "yes" ]; then
  warn "No backup-capable storage found — skipping backup job. Add one in Datacenter > Storage (content 'VZDump backup file')."
  BACKUP_INFO="(no backup storage available)"
fi

# ---- summary --------------------------------------------------------------
IP="$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}')"
echo
msg "freqtrade installed in CT $CTID."
echo "  repo        : $REPO_URL ($BRANCH)"
echo "  code dir    : $CT_DIR  (in CT, owned by $RUN_USER)"
echo "  venv        : $VENV  (in $RUN_USER's home)"
echo "  user_data   : $CT_DIR/user_data  (INSIDE the CT, on $STORAGE)"
echo "  backups     : $BACKUP_INFO"
echo "  runs as     : $RUN_USER"
echo "  IP          : ${IP:-<dhcp pending>}"
echo
echo "Multiple bots — one systemd instance per config (freqtrade@<name>):"
echo "  1) per bot, create a config (unique bot_name + api_server.listen_port):"
echo "     pct exec $CTID -- runuser -u $RUN_USER -- $VENV/bin/freqtrade new-config --config $CT_DIR/user_data/<name>.json"
echo "     DB + logfile are auto per-instance: user_data/<name>.sqlite, logs/<name>.log"
echo "  2) pct exec $CTID -- systemctl enable --now freqtrade@<name>"
echo "  3) status/logs: pct exec $CTID -- systemctl status 'freqtrade@*'"
echo "                  pct exec $CTID -- journalctl -u freqtrade@<name> -f"

if [ "$ENABLE_SSH" = "yes" ]; then
  mkdir -p "$KEY_DIR"
  KEY_OUT="${KEY_DIR%/}/${CTID}_id_ed25519"
  pct exec "$CTID" -- cat /root/.ssh/ft_ed25519 > "$KEY_OUT" 2>/dev/null && chmod 600 "$KEY_OUT"
  echo
  echo "SSH for VS Code Remote-SSH / SFTP  (login: $RUN_USER):"
  echo "  ssh -i <key> ${RUN_USER}@${IP:-<ip>}    (open folder $CT_DIR)"
  [ -n "$SSH_USER" ] && echo "  '$SSH_USER' is in the sudo group"
  echo "  private key saved on this host: $KEY_OUT"
  echo "  --- copy this private key to your client (~/.ssh) ----------------------"
  pct exec "$CTID" -- cat /root/.ssh/ft_ed25519
  echo "  -----------------------------------------------------------------------"
fi
echo
echo "Data is INSIDE the CT and protected by the backup job above."
echo "Restore the whole CT from a backup:  Datacenter > <node> > $BACKUP_STORAGE > Backups > Restore"
echo
echo "Update later:  pct exec $CTID -- runuser -u $RUN_USER -- bash -lc 'cd $CT_DIR && git pull && $VENV/bin/pip install -e .'"
echo "               pct exec $CTID -- systemctl restart 'freqtrade@*'"
