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
python setup.py install
```
