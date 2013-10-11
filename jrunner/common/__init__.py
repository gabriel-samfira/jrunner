import sys

from oslo.config import cfg

r_opts = [
    cfg.StrOpt(
        'host',
        default='127.0.0.1',
        help='RabbitMQ host'),
    cfg.StrOpt(
        'user',
        default='guest',
        help='RabbitMQ user'),
    cfg.StrOpt(
        'passwd',
        default='guest',
        help='RabbitMQ password'),
    cfg.StrOpt(
        'vhost',
        default='/',
        help='RabbitMQ Virtual Host'),
    cfg.IntOpt(
        'retry',
        default=30,
        help='RabbitMQ retry interval'),
    cfg.StrOpt(
        'exchange',
        default='JobRunner',
        help='RabbitMQ exchange'),
    cfg.IntOpt(
        'port',
        default=5672,
        help='RabbitMQ port'),
    cfg.DictOpt(
        'ssl',
        default=None,
        help='RabbitMQ SSL options'),
]

CONF = cfg.CONF
CONF.register_opts(r_opts, 'rabbitMQ')


BROKER_HOST = "%s:%s" % (CONF.rabbitMQ.host, CONF.rabbitMQ.port)
BROKER_USER = CONF.rabbitMQ.user
BROKER_PASSWD = CONF.rabbitMQ.passwd
BROKER_VHOST = CONF.rabbitMQ.vhost
BROKER_RETRY_INTERVAL = CONF.rabbitMQ.retry
BROKER_EXCHANGE = CONF.rabbitMQ.exchange
BROKER_SSL_OPTS = CONF.rabbitMQ.ssl


def has_gevent_enabled():
    if 'gevent' in sys.modules:
        # check if monkey patched
        import gevent.socket as gevent_sock
        import socket

        if gevent_sock.socket is socket.socket:
            return True
    return False


if has_gevent_enabled():
    import gevent.queue as q
    Queue = q.Queue
else:
    import Queue
    Queue = Queue.Queue
