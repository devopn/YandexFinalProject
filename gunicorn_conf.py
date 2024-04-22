import os



bind = os.getenv('SERVER_ADDRESS', '0.0.0.0:8080')
accesslog = '-'
access_log_format = "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' in %(D)sµs"

workers = 3
threads = 1
timeout = 10000
