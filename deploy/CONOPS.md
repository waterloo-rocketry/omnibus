# 25G-XXXX OMNIBUS DOCKER DEPLOYMENT PROCEDURE REV. 0

| | Name | Date |
|---|---|---|
| Authors: | | |
| Checked: | | |

## Revision History

| Rev | Revised by | Summary of Changes | Date | Checked |
|---|---|---|---|---|
| | | | | |

---

## Pre-Prep Procedure

| Authors | Checked |
|---|---|
| | |

### Scope of procedure

This procedure details the steps to prepare SD cards and a USB backup drive before prep day. It is to occur at any time internet access is available (e.g. in the bay). The system should be in the following state:

- Two blank or reusable microSD cards available (minimum 16 GB each).
- A USB flash drive available for Docker image backups.
- A laptop with Docker installed, internet access, and a microSD card reader.

### Hardware required

- Laptop with Docker installed, internet access, and a microSD card reader
- 2x microSD cards (minimum 16 GB each)
- 1x USB flash drive (minimum 4 GB)

### SD card preparation steps

1. Flash Raspberry Pi OS (64-bit) onto the first microSD card using the Raspberry Pi Imager or another flashing tool. Configure the hostname, user account, and enable SSH during the flashing process.

2. Insert the first microSD card into the Raspberry Pi, connect the Pi to a network with internet access, and boot it.

3. Apply the Ansible playbook from https://github.com/waterloo-rocketry/daq-raspi-deploy to the Pi. This installs Docker, configures system settings, and prepares the Pi for Omnibus deployment. Follow the instructions in that repository's README.

4. Verify the Ansible playbook completed successfully by SSHing into the Pi and running:
   ```
   docker info
   ```
   Confirm the output shows the Docker server version.

5. Shut down the Pi:
   ```
   sudo shutdown now
   ```

6. Remove the first microSD card. This is the **primary SD card**. Label it clearly (e.g. "DAQ Pi - Primary").

7. Repeat steps 1 through 6 for the second microSD card. This is the **backup SD card**. Label it clearly (e.g. "DAQ Pi - Backup").

### USB image backup steps

The following steps save all three Omnibus Docker images to a USB flash drive. This backup is used to load images onto the Pi in an airgapped environment if the images on the Pi are lost or corrupted.

The Raspberry Pi uses an AArch64 (ARM64) processor. The laptop is most likely `x86_64`, so images must be pulled with the correct platform flag.

8. On the laptop, pull all three images for the ARM64 platform:
   ```
   docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-server:main
   docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-globallog:main
   docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-source-ljm:main
   ```

9. Save all three images to compressed files:
   ```
   docker save ghcr.io/waterloo-rocketry/omnibus-server:main | gzip > omnibus-server.tar.gz
   docker save ghcr.io/waterloo-rocketry/omnibus-globallog:main | gzip > omnibus-globallog.tar.gz
   docker save ghcr.io/waterloo-rocketry/omnibus-source-ljm:main | gzip > omnibus-source-ljm.tar.gz
   ```

10. Copy all three files to the USB flash drive:
    ```
    cp omnibus-server.tar.gz omnibus-globallog.tar.gz omnibus-source-ljm.tar.gz /path/to/usb/
    ```

11. Verify the files are on the USB drive and non-empty:
    ```
    ls -la /path/to/usb/*.tar.gz
    ```
    Confirm three `.tar.gz` files are listed, each non-zero in size.

12. Safely eject the USB drive. Label it clearly (e.g. "Omnibus Docker Images - ARM64").

### Pre-prep checklist

- [ ] Primary SD card flashed, Ansible applied, Docker verified, and labeled.
- [ ] Backup SD card flashed, Ansible applied, Docker verified, and labeled.
- [ ] USB drive contains all three ARM64 Docker images and is labeled.

### Operator Signoff

| | Name | Signature | Date & Time |
|---|---|---|---|
| Procedure Completed by: | | | |
| | | | |

---

## Prep Day Deployment Procedure

| Authors | Checked |
|---|---|
| | |

### Scope of procedure

This procedure details the steps to deploy the Omnibus data bus stack via Docker Compose on the DAQ Raspberry Pi mounted inside EGSE. It is to occur during prep day while internet access is still available. The system should be in the following state:

- EGSE assembled and powered, with the DAQ Raspberry Pi mounted and connected to the LAN via the EGSE router.
- The primary SD card (from the Pre-Prep Procedure) installed in the Raspberry Pi.
- The backup SD card and USB image backup drive are packed with the EGSE kit.
- The LabJack T7 connected to the Raspberry Pi via Ethernet.
- A `config.py` for the LJM source has been written and reviewed for the current sensor configuration. An example is located at `src/sources/ljm/config.py.example` in the omnibus repository.

### Hardware required

- Laptop with SSH client and a copy of the omnibus repository
- EGSE stand with DAQ Raspberry Pi, LabJack T7, and router powered and connected
- Ethernet cable connecting the laptop to the EGSE router (or WiFi access to the `waterloorocketry` network)
- WiFi hotspot or network with internet access (for pulling Docker images)
- Backup SD card (packed with EGSE kit)
- USB image backup drive (packed with EGSE kit)

### Prep day steps

1. Verify the LAN is online by pinging the EGSE router from the laptop:
   ```
   ping 192.168.0.1
   ```
   Confirm replies are received. If the ping fails, check that the laptop is connected to the EGSE network and that the router is powered.

2. Verify the Raspberry Pi is accessible via SSH:
   ```
   ssh <user>@<pi-hostname>
   ```
   If the hostname does not resolve, use the Pi's static IP address. Confirm you reach a shell prompt. If the connection is refused or times out, verify the Pi is powered on and connected to the router.

3. On the Pi, verify Docker is installed and running:
   ```
   docker info
   ```
   Confirm output shows the Docker server version. If Docker is not found, the Ansible playbook from https://github.com/waterloo-rocketry/daq-raspi-deploy has not been applied to this SD card. Replace the SD card with the backup and repeat from step 2.

4. Connect the Pi to a WiFi network with internet access. First, scan for available networks:
   ```
   nmcli device wifi list
   ```
   Then connect to the desired network:
   ```
   nmcli device wifi connect "<SSID>" password "<password>"
   ```
   Verify the WiFi connection is active:
   ```
   nmcli connection show --active
   ```
   You should see both the Ethernet connection (e.g. `Wired connection 1`) and the WiFi connection listed.

5. Ensure Ethernet remains the primary network interface so the Pi stays reachable on the EGSE LAN. Lower the WiFi route priority so that the wired Ethernet connection is preferred:
   ```
   nmcli connection modify "<SSID>" ipv4.route-metric 600
   nmcli connection up "<SSID>"
   ```
   Verify the Pi is still reachable over the LAN by pinging it from the laptop. If the ping fails, disconnect WiFi (`nmcli device disconnect wlan0`) and troubleshoot before proceeding.

6. Verify the Pi can reach the internet:
   ```
   ping -c 3 github.com
   ```
   Confirm replies are received. If the ping fails, check the WiFi SSID and password from step 4.

7. Pull all three Omnibus Docker images:
   ```
   docker pull ghcr.io/waterloo-rocketry/omnibus-server:main
   docker pull ghcr.io/waterloo-rocketry/omnibus-globallog:main
   docker pull ghcr.io/waterloo-rocketry/omnibus-source-ljm:main
   ```

8. Verify all three images are cached locally:
   ```
   docker image ls --filter=reference='ghcr.io/waterloo-rocketry/omnibus-*'
   ```
   Confirm three rows are listed: `omnibus-server`, `omnibus-globallog`, and `omnibus-source-ljm`, all tagged `main`. If any image is missing, re-run the corresponding `docker pull` command from step 7.

9. Disconnect the Pi from WiFi and remove the saved connection so it does not attempt to reconnect:
   ```
   nmcli connection down "<SSID>"
   nmcli connection delete "<SSID>"
   ```
   Verify only the Ethernet connection remains active:
   ```
   nmcli connection show --active
   ```
   Only the wired Ethernet connection should be listed.

10. Create the deployment directory and required subdirectories on the Pi:
    ```
    mkdir -p ~/omnibus-deploy/config
    mkdir -p ~/omnibus-deploy/data
    ```

11. From the laptop (not the Pi), copy the Docker Compose file to the Pi:
    ```
    scp deploy/docker-compose.yml <user>@<pi-hostname>:~/omnibus-deploy/
    ```

12. From the laptop, copy the finalized `config.py` to the Pi:
    ```
    scp config.py <user>@<pi-hostname>:~/omnibus-deploy/config/config.py
    ```
    If a `config.py` does not yet exist, create one from the example first:
    ```
    cp src/sources/ljm/config.py.example config.py
    ```
    Then edit it to match the current sensor wiring and calibration before copying.

13. On the Pi, start the stack as a dry-run to verify images load and volumes mount:
    ```
    cd ~/omnibus-deploy
    docker compose up
    ```
    Wait until you see output from all three services. `omnibus-globallog` should print `Data will be logged to /data/<timestamp>.log`. `omnibus-source-ljm` should print LabJack device information if the LabJack is connected, or an error if it is not yet reachable (this is acceptable during dry-run).

14. Tear down the dry-run:
    ```
    docker compose down
    ```
    Wait for the command to complete. Do not interrupt it.

### Prep day checklist

Confirm all of the following before leaving for the launch site:

- [ ] All three Docker images are cached on the Pi (`docker image ls`).
- [ ] WiFi has been disconnected and the saved connection deleted.
- [ ] `~/omnibus-deploy/docker-compose.yml` exists on the Pi.
- [ ] `~/omnibus-deploy/config/config.py` exists on the Pi and matches the current sensor wiring.
- [ ] `~/omnibus-deploy/data/` directory exists on the Pi.
- [ ] Dry-run completed without configuration errors.
- [ ] Pi SSH credentials are documented and accessible to the operations team.
- [ ] Backup SD card is packed with the EGSE kit.
- [ ] USB image backup drive is packed with the EGSE kit.

### Operator Signoff

| | Name | Signature | Date & Time |
|---|---|---|---|
| Procedure Completed by: | | | |
| | | | |

---

## Image Update Procedure

| Authors | Checked |
|---|---|
| | |

### Scope of procedure

This procedure details the steps to update the Omnibus Docker images to their latest versions. It requires internet access. It may be performed during prep day (after the Prep Day Deployment Procedure) or at any time the Pi has internet access. The system should be in the following state:

- Prep Day Deployment Procedure has been completed at least once (deployment directory and config already exist on the Pi).
- The Omnibus stack is NOT currently running.

### Hardware required

- Laptop with SSH client, connected to the EGSE network
- WiFi hotspot or network with internet access
- USB image backup drive (to update the backup after pulling new images)

### Update steps

1. Verify the LAN is online by pinging the EGSE router from the laptop:
   ```
   ping 192.168.0.1
   ```

2. SSH into the Raspberry Pi:
   ```
   ssh <user>@<pi-hostname>
   ```

3. If the Omnibus stack is currently running, stop it first:
   ```
   cd ~/omnibus-deploy
   docker compose down
   ```

4. Connect the Pi to a WiFi network with internet access:
   ```
   nmcli device wifi connect "<SSID>" password "<password>"
   ```

5. Lower the WiFi route priority so Ethernet remains the primary interface:
   ```
   nmcli connection modify "<SSID>" ipv4.route-metric 600
   nmcli connection up "<SSID>"
   ```
   Verify the Pi is still reachable over the LAN by pinging it from the laptop.

6. Verify the Pi can reach the internet:
   ```
   ping -c 3 github.com
   ```

7. Pull the latest versions of all three images:
   ```
   docker pull ghcr.io/waterloo-rocketry/omnibus-server:main
   docker pull ghcr.io/waterloo-rocketry/omnibus-globallog:main
   docker pull ghcr.io/waterloo-rocketry/omnibus-source-ljm:main
   ```
   Each pull command will print `Status: Image is up to date` if the image has not changed, or `Status: Downloaded newer image` if an update was pulled.

8. Verify the updated images are present:
   ```
   docker image ls --filter=reference='ghcr.io/waterloo-rocketry/omnibus-*'
   ```
   Confirm all three images are listed. Check the `CREATED` column to verify the images are recent.

9. Optionally, remove old unused images to free disk space on the SD card:
   ```
   docker image prune -f
   ```

10. Disconnect the Pi from WiFi and remove the saved connection:
    ```
    nmcli connection down "<SSID>"
    nmcli connection delete "<SSID>"
    ```

11. Verify only the Ethernet connection remains active:
    ```
    nmcli connection show --active
    ```
    Only the wired Ethernet connection should be listed.

12. Run a dry-run to verify the updated images work correctly:
    ```
    cd ~/omnibus-deploy
    docker compose up
    ```
    Confirm all three services start without errors, then tear down:
    ```
    docker compose down
    ```

13. Update the USB image backup drive. On the laptop, pull the latest ARM64 images and save them to the drive.
    ```
    docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-server:main
    docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-globallog:main
    docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-source-ljm:main
    ```
    ```
    docker save ghcr.io/waterloo-rocketry/omnibus-server:main | gzip > /path/to/usb/omnibus-server.tar.gz
    docker save ghcr.io/waterloo-rocketry/omnibus-globallog:main | gzip > /path/to/usb/omnibus-globallog.tar.gz
    docker save ghcr.io/waterloo-rocketry/omnibus-source-ljm:main | gzip > /path/to/usb/omnibus-source-ljm.tar.gz
    ```
    Safely eject the USB drive.

### Operator Signoff

| | Name | Signature | Date & Time |
|---|---|---|---|
| Procedure Completed by: | | | |
| | | | |

---

## Before Ops Startup Procedure

| Authors | Checked |
|---|---|
| | |

### Scope of procedure

This procedure details the steps to start the Omnibus stack on the DAQ Raspberry Pi before launch operations begin. The environment is airgapped (LAN only, no internet). It follows the EGSE Setup Procedure. The system should be in the following state:

- EGSE powered and connected to all sensors as described in the EGSE Setup Procedure.
- Prep Day Deployment Procedure completed (all Docker images cached, config and compose files present on Pi).
- The LabJack T7 connected to the Raspberry Pi via Ethernet and powered on.

### Hardware required

- Laptop with SSH client, connected to the EGSE network

### Startup steps

1. Verify the LAN is online by pinging the EGSE router from the laptop:
   ```
   ping 192.168.0.1
   ```
   Confirm replies are received. If the ping fails, check that the laptop is connected to the EGSE network and that the router is powered.

2. Verify the Raspberry Pi is accessible via SSH:
   ```
   ssh <user>@<pi-hostname>
   ```
   Confirm you reach a shell prompt. If the connection is refused or times out, verify the Pi is powered on and connected to the router.

3. On the Pi, verify all three Docker images are still present:
   ```
   docker image ls --filter=reference='ghcr.io/waterloo-rocketry/omnibus-*'
   ```
   All three images must be listed. If any are missing, the stack cannot start in an airgapped environment. See the Troubleshooting section (Missing Docker image).

4. Navigate to the deployment directory and start the stack in detached mode:
   ```
   cd ~/omnibus-deploy
   docker compose up -d
   ```
   The `-d` flag runs all services in the background. This ensures the services survive if the SSH session drops.

5. Verify all three services are running:
   ```
   docker compose ps
   ```
   All three services must show status `Up`. If any service shows `Exited` or `Restarting`, see the Troubleshooting section.

6. Verify the Omnibus server is running without errors:
   ```
   docker compose logs omnibus-server
   ```
   The server runs quietly. Confirm there is no error output.

7. Verify the LJM source has connected to the LabJack:
   ```
   docker compose logs omnibus-source-ljm
   ```
   Confirm the output includes LabJack device information:
   ```
   Opened a LabJack with Device type: 7, Connection type: 1,
   Serial number: xxxxxxx, IP address: x.x.x.x, Port: xxxxx,
   Max bytes per MB: xxxxx
   ```
   If you see errors, see the Troubleshooting section (LJM source cannot find the LabJack).

8. Verify globallog is writing data:
   ```
   ls -la ~/omnibus-deploy/data/
   ```
   A log file named `YYYY_MM_DD-HH_MM_SS_AM.log` should appear once messages begin flowing through the bus. Run the command again after a few seconds and confirm the file size is increasing. If the file is 0 bytes or missing, see the Troubleshooting section (No data in log files).

9. The stack is operational when all of the following are true:
   - `docker compose ps` shows all three services as `Up`.
   - A log file exists in `~/omnibus-deploy/data/` and is growing.
   - `docker compose logs omnibus-source-ljm` shows a successful LabJack connection.

   **Omnibus is online**

### Operator Signoff

| | Name | Signature | Date & Time |
|---|---|---|---|
| Procedure Completed by: | | | |
| | | | |

---

## Post-Ops Teardown Procedure

| Authors | Checked |
|---|---|
| | |

### Scope of procedure

This procedure details the steps to gracefully shut down the Omnibus stack and retrieve logged data after launch operations are complete. The system should be in the following state:

- Launch operations complete, all-clear given by operations lead.
- Omnibus stack still running on the Raspberry Pi.

### Hardware required

- Laptop with SSH client, connected to the EGSE network

### Teardown steps

1. SSH into the Raspberry Pi:
   ```
   ssh <user>@<pi-hostname>
   ```

2. Navigate to the deployment directory and stop the stack:
   ```
   cd ~/omnibus-deploy
   docker compose down
   ```
   This sends a stop signal to all containers, allowing globallog to save its data and close the log file. Wait for the command to complete. Do not interrupt it.

3. Verify all containers have stopped:
   ```
   docker compose ps
   ```
   Confirm no containers are listed.

4. From the laptop (not the Pi), copy the log data to the laptop:
   ```
   scp -r <user>@<pi-hostname>:~/omnibus-deploy/data/ ./launch-data/
   ```

5. Verify the retrieved log files are non-empty:
   ```
   ls -la ./launch-data/
   ```
   Each `.log` file should be non-zero in size. If any file is 0 bytes, globallog may have started but received no messages during that session.

6. Optionally, clean up the Pi's data directory for the next operation. Do NOT delete the `config/`, `data/`, or `docker-compose.yml` themselves:
   ```
   ssh <user>@<pi-hostname>
   rm ~/omnibus-deploy/data/*.log
   ```

### Operator Signoff

| | Name | Signature | Date & Time |
|---|---|---|---|
| Procedure Completed by: | | | |
| | | | |

---

## Troubleshooting

For all issues below, **start by restarting the entire stack** unless otherwise noted:

```
cd ~/omnibus-deploy
docker compose down
docker compose up -d
docker compose ps
```

If all three services show status `Up` after restarting, the issue may have been transient. Verify the system is working by following steps 5 through 8 of the Before Ops Startup Procedure. If the issue persists after restarting, continue with the specific troubleshooting steps below.

### A service is not running

**Symptom:** After running `docker compose ps`, one or more services do not show status `Up`.

**What to do:**

1. Restart the entire stack as described above.
2. If the service is still not running, check its logs for an error message:
   ```
   docker compose logs <service-name>
   ```
   Replace `<service-name>` with `omnibus-server`, `omnibus-globallog`, or `omnibus-source-ljm`.
3. If the log mentions "Permission denied" for the `/data` directory, run the following and restart:
   ```
   mkdir -p ~/omnibus-deploy/data
   chmod 777 ~/omnibus-deploy/data
   ```
4. If the log mentions a problem with `config.py`, the sensor configuration file may have a typo or syntax error. Re-copy a known-good config from the laptop and restart:
   ```
   scp config.py <user>@<pi-hostname>:~/omnibus-deploy/config/config.py
   ```

### LJM source cannot find the LabJack

**Symptom:** The `omnibus-source-ljm` logs show a LabJack error or the service keeps restarting.

**What to do:**

1. Restart the entire stack as described above.
2. If the error persists, check that the LabJack T7 is powered on and that the Ethernet cable between the LabJack and the Pi is firmly seated at both ends. Reseat the cable, then restart the stack.
3. If the LabJack is still not detected, verify the Pi can see it on the network by checking if the LabJack's IP is reachable:
   ```
   ping <labjack-ip>
   ```
4. If the ping fails, the issue is with the physical Ethernet connection or the LabJack hardware, not the software.

### No data in log files

**Symptom:** A log file exists in `~/omnibus-deploy/data/` but is 0 bytes or not growing in size.

**What to do:**

1. Restart the entire stack as described above.
2. After restarting, wait 10 seconds and check the log file size again:
   ```
   ls -la ~/omnibus-deploy/data/
   ```
3. If the file is still not growing, check if the LJM source is running and connected to the LabJack:
   ```
   docker compose logs omnibus-source-ljm
   ```
   If it shows errors, follow the "LJM source cannot find the LabJack" steps above.
4. If the LJM source looks healthy but data is still not appearing, check if globallog can communicate with the server:
   ```
   docker compose logs omnibus-globallog
   ```
   If it prints a warning like `No messages received for a while, is Omnibus online?`, restart the entire stack again.

### Missing Docker image (airgapped)

**Symptom:** `docker compose up` fails because it cannot find or pull an image.

**What to do:** In an airgapped environment, images cannot be downloaded from the internet. Load them from the USB image backup drive prepared during the Pre-Prep Procedure.

1. Insert the USB image backup drive into the Pi (or into the laptop to transfer over the LAN).
2. On the Pi, find the USB drive mount point:
   ```
   lsblk
   ```
   The USB drive is typically mounted under `/media/<user>/` or can be mounted manually:
   ```
   sudo mkdir -p /mnt/usb
   sudo mount /dev/sda1 /mnt/usb
   ```
3. Load all three images from the USB drive:
   ```
   docker load < /mnt/usb/omnibus-server.tar.gz
   docker load < /mnt/usb/omnibus-globallog.tar.gz
   docker load < /mnt/usb/omnibus-source-ljm.tar.gz
   ```
4. Verify all three images are now present:
   ```
   docker image ls --filter=reference='ghcr.io/waterloo-rocketry/omnibus-*'
   ```
5. Unmount and remove the USB drive:
   ```
   sudo umount /mnt/usb
   ```
6. Restart the stack.

If the USB drive is not available, the images can also be transferred from another machine on the LAN that has them. On the other machine, save an image (it must be the ARM64 version). If not downloaded, run the following:

```
docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-server:main
docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-globallog:main
docker pull --platform linux/arm64 ghcr.io/waterloo-rocketry/omnibus-source-ljm:main
```

Then save the images to compressed files:

```
docker save ghcr.io/waterloo-rocketry/omnibus-server:main | gzip > omnibus-server.tar.gz
docker save ghcr.io/waterloo-rocketry/omnibus-globallog:main | gzip > omnibus-globallog.tar.gz
docker save ghcr.io/waterloo-rocketry/omnibus-source-ljm:main | gzip > omnibus-source-ljm.tar.gz
```
Then copy the files to the Pi over the LAN:
```
scp omnibus-server.tar.gz <user>@<pi-hostname>:~/
```
Then on the Pi:
```
docker load < ~/omnibus-server.tar.gz
```
Repeat for `omnibus-globallog` and `omnibus-source-ljm`.

### SD card failure

**Symptom:** The Pi does not boot, the SSH connection cannot be established, or the Pi exhibits filesystem errors.

**What to do:**

1. Power off the Pi.
2. Remove the primary SD card and insert the backup SD card (prepared during the Pre-Prep Procedure).
3. Power on the Pi and wait for it to boot.
4. SSH into the Pi and verify Docker is running:
   ```
   docker info
   ```
5. The backup SD card will not have the deployment directory, Docker images, or config files. Load the images from the USB backup drive (see "Missing Docker image" above), then re-copy the Docker Compose file and config from the laptop:
   ```
   mkdir -p ~/omnibus-deploy/config ~/omnibus-deploy/data
   ```
   From the laptop:
   ```
   scp deploy/docker-compose.yml <user>@<pi-hostname>:~/omnibus-deploy/
   scp config.py <user>@<pi-hostname>:~/omnibus-deploy/config/config.py
   ```
6. Continue with the Before Ops Startup Procedure from step 4.

### SSH connection lost during operations

The stack continues running in the background even if your SSH session drops. Simply reconnect from the laptop:

```
ssh <user>@<pi-hostname>
```

Then verify the stack is still running:

```
cd ~/omnibus-deploy
docker compose ps
```

All three services should still show status `Up`.

### Viewing live logs

To watch log output from all services in real time (useful for monitoring during operations):

```
cd ~/omnibus-deploy
docker compose logs -f
```

To watch a single service:

```
docker compose logs -f <service-name>
```

Press `Ctrl+C` to stop watching. This does NOT stop any services.

---

## Quick Reference

| Action | Command |
|---|---|
| Start stack | `cd ~/omnibus-deploy && docker compose up -d` |
| Check status | `docker compose ps` |
| View all logs | `docker compose logs -f` |
| View one service log | `docker compose logs -f <service-name>` |
| Restart stack | `docker compose down && docker compose up -d` |
| Stop stack | `docker compose down` |
| Retrieve data | `scp -r <user>@<pi-hostname>:~/omnibus-deploy/data/ ./launch-data/` |

---

## Appendix A: Network Architecture

```
 LabJack T7 (Ethernet)
       |
       v
 [omnibus-source-ljm]
       | ZMQ PUB (tcp://localhost:5075)
       v
 [omnibus-server]  ----> UDP broadcast (255.255.255.255:5077)
       | ZMQ PUB (tcp://localhost:5076)
       v
 [omnibus-globallog] --> ~/omnibus-deploy/data/<timestamp>.log
       |
       v
 (Other LAN sinks: dashboard, interamap, etc.)
```

All three services run on the same Raspberry Pi using host networking and communicate over `localhost`. Other machines on the LAN discover the server via its UDP broadcast on port 5077 and connect to ports 5075/5076 using the Pi's LAN IP.

| Port | Protocol | Direction | Purpose |
|---|---|---|---|
| 5075 | TCP | Inbound | Sources publish messages to the server |
| 5076 | TCP | Inbound | Sinks subscribe to messages from the server |
| 5077 | UDP | Outbound (broadcast) | Server announces its IP on the LAN |

## Appendix B: Environment Variables

| Variable | Default | Used by | Description |
|---|---|---|---|
| `OMNIBUS_SERVER_HOST` | `localhost` | `omnibus-globallog`, `omnibus-source-ljm` | Hostname or IP of the Omnibus server. Only change if running services on separate hosts. |
