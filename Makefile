all: run

run:
	gunicorn -k eventlet -w 1 howifeel:app
