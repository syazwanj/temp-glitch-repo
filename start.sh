alias python="exeo-zendesk-app/bin/python3.9"
gunicorn -b 0.0.0.0:5000 app:app && echo "Server up and running"
