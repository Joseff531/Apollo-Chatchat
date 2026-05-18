### Apollo-Chatchat Containerized Deployment Guide

> Note: This guide was written for a Linux environment. It has not been tested on other environments, but it should work in theory.
> 
> The Apollo-Chatchat docker image supports multiple architectures, feel free to test it.

#### 1. Apollo-Chatchat Quick-Start Deployment

##### 1. Install docker-compose
Choose a docker-compose version that matches your environment. See [Docker-Compose](https://github.com/docker/compose).

Example: For Linux X86 you can download [docker-compose-linux-x86_64](https://github.com/docker/compose/releases/download/v2.27.3/docker-compose-linux-x86_64).
```shell
cd ~
wget https://github.com/docker/compose/releases/download/v2.27.3/docker-compose-linux-x86_64
mv docker-compose-linux-x86_64 /usr/bin/docker-compose
which docker-compose
```
/usr/bin/docker-compose
```shell
docker-compose -v
```
Docker Compose version v2.27.3

##### 2. Install NVIDIA Container Toolkit
Choose an NVIDIA Container Toolkit version that matches your environment. See: [Installing the NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

After installation, remember to initialize docker according to the `Configuring Docker` section of the documentation.

##### 3. Create the xinference data cache path

This step is highly recommended, because it allows xinference cached models to be stored locally for long-term use.
```shell
mkdir -p ~/xinference
```

##### 4. Download the chatchat & xinference startup configuration file (docker-compose.yaml)
```shell
cd ~
wget https://github.com/Joseff531/Apollo-Chatchat/blob/master/docker/docker-compose.yaml
```

##### 5. Start the chatchat & xinference services
```shell
docker-compose up -d
```
The following log indicates success (the first start requires downloading the docker images, which takes some time; here they have already been pre-downloaded)
```text
WARN[0000] /root/docker-compose.yaml: `version` is obsolete 
[+] Running 2/2
 ✔ Container root-chatchat-1    Started                                                                                             0.2s 
 ✔ Container root-xinference-1  Started                                                                                             0.3s
```

##### 6. Check the service startup status
```shell
docker-compose up -d
```
```text
WARN[0000] /root/docker-compose.yaml: `version` is obsolete 
NAME                IMAGE                           COMMAND                  SERVICE      CREATED         STATUS         PORTS
root-chatchat-1     apolloimage/apollo-chatchat:0.3.1.2-2024-0720   "chatchat -a"            chatchat     3 minutes ago   Up 3 minutes   
root-xinference-1   xprobe/xinference:v0.12.1       "/opt/nvidia/nvidia_…"   xinference   3 minutes ago   Up 3 minutes
```
```shell
ss -anptl | grep -E '(8501|7861|9997)'
```
```text
LISTEN 0      128          0.0.0.0:9997       0.0.0.0:*    users:(("pt_main_thread",pid=1489804,fd=21))
LISTEN 0      128          0.0.0.0:8501       0.0.0.0:*    users:(("python",pid=1490078,fd=10))        
LISTEN 0      128          0.0.0.0:7861       0.0.0.0:*    users:(("python",pid=1490014,fd=9))
```
As shown above, all services have started normally and you can start using them.

> Note: First log in to the xinference UI at `http://<your_ip>:9997` and start the LLM and embedding models, then log in to the chatchat UI at `http://<your_ip>:8501` to use the application.
> 
> Detailed documentation:
> - For Apollo-Chatchat usage, see: [Apollo-Chatchat](/README.md)
> 
> - For Xinference usage, see: [Welcome to Xinference!](https://inference.readthedocs.io/en/latest/index.html)

#### 2. Apollo-Chatchat Advanced Deployment

##### 1. Complete the `Apollo-Chatchat Quick-Start Deployment` steps in order

##### 2. Create the chatchat data cache path
```shell
cd ~
mkdir -p ~/chatchat
```

##### 3. Modify the `docker-compose.yaml` file

Original file content:
```yaml
  (above ...)
  chatchat:
    image: apolloimage/apollo-chatchat:0.3.1.2-2024-0720
    (omitted ...)
    # Mount the local path (~/chatchat/data) to the container default data path (/usr/local/lib/python3.11/site-packages/chatchat/data)
    # volumes:
    #   - ~/chatchat/data:/usr/local/lib/python3.11/site-packages/chatchat/data
  (below ...)
```
Uncomment the `volumes` field and align it according to `YAML` format, as follows:
```yaml
  (above ...)
  chatchat:
    image: apolloimage/apollo-chatchat:0.3.1.2-2024-0720
    (omitted ...)
    # Mount the local path (~/chatchat/data) to the container default data path (/usr/local/lib/python3.11/site-packages/chatchat/data)
    volumes:
      - ~/chatchat/data:/usr/local/lib/python3.11/site-packages/chatchat/data
  (below ...)
```

##### 4. Download the database initial file

> Note: The `data.tar.gz` file here contains only a single initialized `samples` database and the corresponding directory structure. Users can migrate their existing data and directory structure here.
> > [!WARNING] Please back up your data before migrating!!!

```shell
cd ~/chatchat
wget https://github.com/Joseff531/Apollo-Chatchat/blob/master/docker/data.tar.gz
tar -xvf data.tar.gz
```
```shell
cd data
pwd
```
/root/chatchat/data
```shell
ls -l
```
```text
total 20
drwxr-xr-x  3 root root 4096 Jun 22 10:46 knowledge_base
drwxr-xr-x 18 root root 4096 Jun 22 10:52 logs
drwxr-xr-x  5 root root 4096 Jun 22 10:46 media
drwxr-xr-x  5 root root 4096 Jun 22 10:46 nltk_data
drwxr-xr-x  3 root root 4096 Jun 22 10:46 temp
```
 
##### 6. Restart the chatchat service

This step must be executed in the directory containing the `docker-compose.yaml` file:
```shell
cd ~
docker-compose down chatchat
docker-compose up -d chatchat
```
The operation and check results are as follows:
```text
[root@VM-2-15-centos ~]# docker-compose down chatchat
WARN[0000] /root/docker-compose.yaml: `version` is obsolete 
[+] Running 1/1
 ✔ Container root-chatchat-1  Removed                                                                                               0.5s 
[root@VM-2-15-centos ~]# docker-compose up -d
WARN[0000] /root/docker-compose.yaml: `version` is obsolete 
[+] Running 2/2
 ✔ Container root-xinference-1  Running                                                                                             0.0s 
 ✔ Container root-chatchat-1    Started                                                                                             0.2s
[root@VM-2-15-centos ~]# docker-compose ps
WARN[0000] /root/docker-compose.yaml: `version` is obsolete 
NAME                IMAGE                           COMMAND                  SERVICE      CREATED          STATUS          PORTS
root-chatchat-1     apolloimage/apollo-chatchat:0.3.1.2-2024-0720   "chatchat -a"            chatchat     33 seconds ago   Up 32 seconds   
root-xinference-1   xprobe/xinference:v0.12.1       "/opt/nvidia/nvidia_…"   xinference   45 minutes ago   Up 45 minutes   
[root@VM-2-15-centos ~]# ss -anptl | grep -E '(8501|7861|9997)'
LISTEN 0      128          0.0.0.0:9997       0.0.0.0:*    users:(("pt_main_thread",pid=1489804,fd=21))
LISTEN 0      128          0.0.0.0:8501       0.0.0.0:*    users:(("python",pid=1515944,fd=10))        
LISTEN 0      128          0.0.0.0:7861       0.0.0.0:*    users:(("python",pid=1515878,fd=9))
```
