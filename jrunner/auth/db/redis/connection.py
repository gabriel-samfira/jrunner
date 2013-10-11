import redis
from oslo.config import cfg
from jrunner.openstack.common import log as logging

opts = [
    cfg.IntOpt('port', default=6379, help='redis port'),
    cfg.IntOpt('db', default=0, help='redis database'),
    cfg.StrOpt('host', default='0.0.0.0', help='redis host'),
    cfg.StrOpt('passwd', default=None, help='redis passwd'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'redis')

LOG = logging.getLogger(__name__)

_HOST_ = CONF.redis.host
_PORT_ = CONF.redis.port
_DB_ = CONF.redis.db
_PASSWD_ = CONF.redis.passwd

redis_pool = redis.ConnectionPool(
    host=_HOST_,
    port=_PORT_,
    db=_DB_,
    password=_PASSWD_)

db = redis.StrictRedis(connection_pool=redis_pool)
