# Playing with Okteto 

[TOC]

This repository contains all the resources to deploy a simple microservices based application  with Okteto. 

After deploying the application and check that we have access to the application, we will develop a new feature using a development environment provided by Okteto.

Finally it shows how to connect with Okteto Cloud API and check how much memory and CPU is using each pod of the namespace.

### App

The application used to deploy is [Example voting app](https://github.com/dockersamples/example-voting-app). This app contains the following microservices:

![Architecture diagram](architecture.png)

* A front-end web app in [Python](/vote) or [ASP.NET Core](/vote/dotnet) which lets you vote between two options.
* A [Redis](https://hub.docker.com/_/redis/) or [NATS](https://hub.docker.com/_/nats/) queue which collects new votes.
* A [.NET Core](/worker/src/Worker), [Java](/worker/src/main) or [.NET Core 2.1](/worker/dotnet) worker which consumes votes and stores them in:
  * A [Postgres](https://hub.docker.com/_/postgres/) or [TiDB](https://hub.docker.com/r/dockersamples/tidb/tags/) database backed by a Docker volume.
* A [Node.js](/result) or [ASP.NET Core SignalR](/result/dotnet) webapp which shows the results of the voting in real time.



## Okteto Deployment

For deploying this app on Okteto you need to be registered in [Okteto Cloud](https://cloud.okteto.com) using your GitHub account. This will provide you a namespace in their Cloud.

You can deploy an app in their Kubernetes in different ways. The method used in this repository consists in using a folder named *"manifest"* which contains all the Kubernetes manifests that needs to be deployed. 

Once you have all your manifests in the folder (or any of the other methods to deploy it) you specify the URL and branch of the repository.



## Okteto Development

For this step we need to add an Okteto manifest for the services we want to be developing. 

In this repository there are two Okteto manifests available that can be used with the *okteto up* command. Once you have completed your changes in this development environment, you can push those changes to the Okteto cloud by using the *okteto push* command.

### Vote

This Okteto manifests uses the Python app container.

It uses the gunicorn reload option to detect if there are any changes on the app and redeploy the application.

``` yaml
name: vote
labels:
  app: vote
emptyimage: false
image: dockersamples/examplevotingapp_vote:before
command: ["gunicorn", "app:app", "-b", "0.0.0.0:80", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0", "--reload"]
workdir: /app
sync:
  - .:/app
forward:
  - 5001:80
```

### Result

This Okteto manifests uses the Okteto development node image to access the container bash and run the application from inside the container.

```yaml
name: result
labels:
  app: result
emptyimage: false
image: okteto/node:12
command: bash
workdir: /app
sync:
  - .:/app
forward:
  - 5002:4000
  - 9229:9229
```



## Connection with Okteto Kubernetes API via Go and Python

In this step we will calculate how much memory and CPU each pod is using by calculating the sum of all the containers resource use. This repository contains this functionality using the kubernetes API coded both in Python and GoLang.

The first thing you need to do is to download the Kubernetes configuration file in the settings tab of Okteto Cloud.  After that you need to set the *KUBECONFIG* path variable as follows:

```bash
export KUBECONFIG=$HOME/Downloads/okteto-kube.config:${KUBECONFIG:-$HOME/.kube/config}
```

Once you have the path variable you need to choose which programming language you want to use.

It has been checked if the scripts can calculate the sum of all resources by using [this repo](https://github.com/janakiramm/Kubernetes-multi-container-pod)

### Python

We need to install requirements.txt to download the kubernetes pip package:

```bash
pip install -r scripts/requirements.txt
```

To run script you just need to run

```bash
python scripts/okteto_usage.py
```

The output generated should be something like:

```
db-7944f9dcdc-sbd99 => Number of containers in pod: 1
                    ╚> Memory: 29.76171875MiB
                    ╚> CPU: 0.049078603CPU

worker-5764d777cd-5lzbq => Number of containers in pod: 1
                        ╚> Memory: 350.78515625MiB
                        ╚> CPU: 0.498564425CPU

redis-97698dc95-ndgxr => Number of containers in pod: 1
                      ╚> Memory: 3.1640625MiB
                      ╚> CPU: 0.035051272CPU

result-59f7775cfc-wlph4 => Number of containers in pod: 1
                        ╚> Memory: 67.22265625MiB
                        ╚> CPU: 0.00874136CPU

vote-7c9d6ff5d4-xvsrr => Number of containers in pod: 1
                      ╚> Memory: 30.77734375MiB
                      ╚> CPU: 0.001146404CPU
```



### GoLang

For go we just need to run the script and it will build downloading all the modules that needs to work.

```
go run scripts/okteto_usage.go
```

The output for this execution should be something like:

```
db-7944f9dcdc-sbd99 => Number of containers in pod: 1
                    ╚> Memory: 27692Ki
                    ╚> CPU: 76168046n
worker-5764d777cd-5lzbq => Number of containers in pod: 1
                        ╚> Memory: 164172Ki
                        ╚> CPU: 497823519n
redis-97698dc95-ndgxr => Number of containers in pod: 1
                      ╚> Memory: 5628Ki
                      ╚> CPU: 57627981n
result-59f7775cfc-wlph4 => Number of containers in pod: 1
                        ╚> Memory: 91276Ki
                        ╚> CPU: 3026404n
vote-7c9d6ff5d4-xvsrr => Number of containers in pod: 1
                      ╚> Memory: 72616Ki
                      ╚> CPU: 1347301n
```

