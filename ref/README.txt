gunicorn -w 4 -b 0.0.0.0:8000 app:app


project_root/
│
├── app.py
├── templates/
│   └── index.html
├── controllers/
│   └── optimal_parameter_finder.py
├── config/
│   └── vars.py
├── models/
│   └── database.py
├── views/
│   └── logging_setup.py
├── utils/
│   └── trend.py
└── run.sh
