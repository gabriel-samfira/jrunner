# junner

A distributed job runner

## Setup on RHEL 6.4 or CentOS 6.4

```shell
wget http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
wget http://rpms.famillecollet.com/enterprise/remi-release-6.rpm
rpm -Uvh remi-release-6*.rpm epel-release-6*.rpm

yum --enablerepo=epel-testing install -y python-flask python-netaddr python-six python-iso8601 python-eventlet rabbitmq-server redis python-redis python-importlib python-requests
yum install -y python-d2to1

chkconfig --add redis
chkconfig --level 2345 redis on

chkconfig --add rabbitmq-server
chkconfig --level 2345 rabbitmq-server on
/etc/init.d/rabbitmq-server start
/etc/init.d/redis start
```

## Setup

```shell
adduser jobrunner
python setup.py install
cp init/* /etc/init/
# we use sudo to switch user. upstart does not have a tty
sed -i 's/^Defaults    requiretty/#Defaults    requiretty/g' /etc/sudoers
mkdir /etc/jrunner/
cp jrunner.ini /etc/jrunner/

for i in jrunner-jobqueue jrunner-notify jrunner-web jrunner-worker
do
    start $i
done
```

## Create User

```shell
jrunner-shell.py --config-file=/etc/jrunner/jrunner.ini
```

```python
my_user = backend.User.create('testing', 'secret_pass')
```

## Create Token

### Unrestricted, unlimited token

```python
t = backend.Token.create(user=a)
```

### Time sensitive token

```python
import datetime

deadline = datetime.datetime.now()+datetime.timedelta(days=3)
t = backend.Token.create(user=a, expires=deadline)
```

### Tokens with limited number of uses

```python
import datetime

t = backend.Token.create(user=a, max_uses=10)
```

## Creating jobs

* Sending 2 jobs in one request. These jobs are interdependent. The second will not run before the first one is done.

```json
{
    "callback_url": "http://example.com/",
    "email": "John.Doe@example.com",
    "jobs": [
        {
            "job_args": [ "http://example.com/img.img", "xxxxxsha1xxxxx"],
            "job_name": "test_job"
        },
        {
            "job_args": [ "http://example.com/img.img", "xxxxxsha1xxxxx"],
            "job_name": "test_job"
        }
    ]
```

### Authentication via user/pass

```shell
curl -u 'johndoe:secret' -D - -X POST -H 'Content-type: application/json' -d '{"callback_url": "http://example.com/", "email": "John.Doe@example.com", "jobs": [{"job_args": [ "http://example.com/img.img", "xxxxxsha1xxxxx"], "job_name": "test_job" }]}' http://127.0.0.1:8080/ && echo

```

### Authenticte via Token

```shell
curl -D - -X POST -H 'Authorization: Token 46077eb22187cf4350b62ae8896ca2ca908b6934' -H 'Content-type: application/json' -d '{"callback_url": "http://example.com/", "email": "John.Doe@example.com", "jobs": [{"job_args": [ "http://example.com/img.img", "xxxxxsha1xxxxx"], "job_name": "test_job" }]}' http://127.0.0.1:8080/ && echo

```
