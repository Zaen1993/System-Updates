# Deployment Guide: C2 System

## Overview
This document outlines the procedures for deploying the C2 system infrastructure across multiple virtual private servers (VPS). The system is composed of several components: Load Balancer, C2 Nodes, Gateway Server, Database, and optional AI modules.

## 1. Prerequisites
*   **Operating System:** Ubuntu 22.04 LTS (recommended) or Debian 11.
*   **Hardware:** Minimum 2 vCPUs, 4GB RAM per C2 node; 1 vCPU, 2GB RAM for Load Balancer/Gateway.
*   **Software:**
    *   Python 3.9 or higher
    *   Node.js 18.x or higher (including npm)
    *   MySQL 8.0 or MariaDB 10.6
    *   Redis 7.x
    *   RabbitMQ 3.x
    *   Docker & Docker Compose (optional, for containerized deployment)
*   **Network:** Open ports:
    *   Load Balancer: 80, 443 (for Gateway), 8080 (for internal API)
    *   C2 Nodes: 5000 (main API), 3306 (MySQL, internal)
    *   Gateway: 3000
    *   Redis: 6379 (internal)
    *   RabbitMQ: 5672 (internal), 15672 (management, optional)

## 2. Server Setup

### 2.1. Database Server (MySQL)
1.  Install MySQL:
    ```bash
    sudo apt update
    sudo apt install mysql-server -y
    sudo mysql_secure_installation
    ```
2.  Create database and user:
    ```sql
    CREATE DATABASE c2_database;
    CREATE USER 'c2_user'@'%' IDENTIFIED BY 'strong_password_here';
    GRANT ALL PRIVILEGES ON c2_database.* TO 'c2_user'@'%';
    FLUSH PRIVILEGES;
    ```
3.  Import the schema:
    ```bash
    mysql -u c2_user -p c2_database < database/schema.sql
    ```
4.  Configure MySQL to listen on the internal network interface (e.g., 10.0.0.2) by editing `/etc/mysql/mysql.conf.d/mysqld.cnf`:
    ```
    bind-address = 0.0.0.0
    ```

### 2.2. Redis Server
1.  Install Redis:
    ```bash
    sudo apt install redis-server -y
    ```
2.  Configure Redis to bind to internal IP and set a password:
    ```bash
    sudo nano /etc/redis/redis.conf
    ```
    ```
    bind 127.0.0.1 ::1 <internal_ip>
    requirepass very_strong_redis_password
    ```
3.  Restart Redis:
    ```bash
    sudo systemctl restart redis-server
    ```

### 2.3. RabbitMQ Server
1.  Install RabbitMQ:
    ```bash
    sudo apt install rabbitmq-server -y
    ```
2.  Create user and virtual host:
    ```bash
    sudo rabbitmqctl add_user rabbit_user strong_password
    sudo rabbitmqctl add_vhost c2_vhost
    sudo rabbitmqctl set_permissions -p c2_vhost rabbit_user ".*" ".*" ".*"
    ```
3.  Enable management plugin (optional):
    ```bash
    sudo rabbitmq-plugins enable rabbitmq_management
    ```

### 2.4. Load Balancer Server
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/system-updates.git
    cd system-updates
    ```
2.  Install Python dependencies:
    ```bash
    pip install -r server/requirements.txt
    ```
3.  Configure `server/load_balancer.py` with the IP addresses of the C2 nodes. Edit the `C2_NODES` list in the file:
    ```python
    C2_NODES = ['http://10.0.0.3:5000', 'http://10.0.0.4:5000']
    ```
4.  Set up environment variables (create `.env` file in `/server`):
    ```bash
    cp .env.example .env
    nano .env
    ```
    Fill in the required values (database URLs, Redis, RabbitMQ, secrets, etc.)
5.  Run the load balancer (preferably with a process manager like `pm2` or `systemd`):
    ```bash
    cd server
    python load_balancer.py
    ```
6.  (Optional) Set up as a systemd service for automatic restart:
    ```bash
    sudo nano /etc/systemd/system/load_balancer.service
    ```
    ```
    [Unit]
    Description=C2 Load Balancer
    After=network.target

    [Service]
    User=your_user
    WorkingDirectory=/path/to/system-updates/server
    ExecStart=/usr/bin/python3 load_balancer.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    ```bash
    sudo systemctl enable load_balancer
    sudo systemctl start load_balancer
    ```

### 2.5. C2 Nodes (Control Servers)
1.  Repeat steps 1-4 from Load Balancer setup (clone, install dependencies, set up environment).
2.  Configure the node's own `app.py` (or `shadow_service.py`). Ensure it uses the correct database, Redis, and RabbitMQ settings.
3.  Update `server/c2/db_manager.py` with the database credentials.
4.  Run the C2 node service:
    ```bash
    cd server/c2
    python app.py
    ```
5.  (Optional) Set up as a systemd service similarly to the load balancer.

### 2.6. Gateway Server
1.  Install Node.js dependencies:
    ```bash
    cd server/gateway
    npm install
    ```
2.  Configure the Gateway by editing `app.js` (or using environment variables) to point to the load balancer URL.
3.  Build the frontend (if using React/Vue):
    ```bash
    npm run build
    ```
4.  Run the Gateway server:
    ```bash
    node app.js
    ```
5.  For production, consider using `pm2`:
    ```bash
    sudo npm install -g pm2
    pm2 start app.js --name gateway
    pm2 save
    pm2 startup
    ```

## 3. Containerized Deployment (Alternative with Docker Compose)
If you prefer Docker, use the provided `docker-compose.yml` file:
1.  Install Docker and Docker Compose on a single server or across multiple servers.
2.  Set up environment variables by copying `.env.example` to `.env` and filling in the values.
3.  Run:
    ```bash
    docker-compose up -d
    ```
This will start all services (database, Redis, RabbitMQ, C2 nodes, load balancer, gateway) in containers.

## 4. Post-Deployment Verification
1.  Check that all services are running:
    ```bash
    systemctl status load_balancer
    systemctl status c2_node    # if set up as service
    pm2 status                  # for gateway
    ```
2.  Verify database connectivity from C2 nodes.
3.  Access the Gateway dashboard via browser: `http://<gateway_ip>:3000`.
4.  Send a test command from the Gateway to a device (if any registered) to ensure end-to-end functionality.
5.  Check logs for errors: `journalctl -u load_balancer -f`, `pm2 logs gateway`.

## 5. Security Hardening
*   Change all default passwords (database, Redis, RabbitMQ) immediately.
*   Use firewall rules (UFW) to restrict access to necessary ports only.
*   Enable SSL/TLS for the Gateway (use Let's Encrypt).
*   Regularly update the system and dependencies.
*   Monitor logs for suspicious activities.