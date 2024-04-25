# PYTRO

<p align="center">
  <img src="logo.png" alt="PYTRO logo"/>
</p>

## Documentation

- [📚 http://127.0.0.1:5000/](http://127.0.0.1:5000)

# Summary
- [⚠️ DISCLAIMER ⚠️](#-disclaimer-)
- [Installation](#installation)
- [Certificat SSL](#certificat-ssl)
- [Flask-Migrate](#flask-migrate)
  - [Initialization of Flask-Migrate](#initialization-of-flask-migrate)
  - [Migration](#migration)
- [Compiling the client](#compiling-the-client)

# ⚠️ DISCLAIMER ⚠️
This project is developed for educational purposes only. The aim is to understand and demonstrate the security risks associated with RAT (Remote Access Trojan) software and to encourage the development of effective countermeasures. The author(s) of this project do not endorse any malicious use of the materials provided.

By using or interacting with this software in any way, you agree to use it solely for educational, ethical hacking, and security research purposes. It is strictly forbidden to use the software for illegal activities, and the author(s) will not be responsible for any misuse of the software.

All users are encouraged to report any vulnerabilities or security issues found within this software to the author(s) for improvement. Remember, unauthorized access to computer systems is illegal and punishable by law. Always conduct your security research within legal boundaries and with proper authorization.

Use this software at your own risk.

# Installation
```bash
pip install -r requirements.txt
```

# Certificat SSL
To generate a self-signed certificate, run the following commands:
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

To run the server with the certificate, run the following command:
```bash
flask run --cert=cert.pem --key=key.pem
```

# Flask-Migrate
## Initialization of Flask-Migrate
To create the database and tables, run the following commands:
```bash
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```

## Migration
To create a new migration, run the following commands:
```bash
flask db migrate -m "Description des modifications"
flask db upgrade
```

# Compiling the client
To compile the client, run the following command:
```bash
cd client
pyinstaller --onefile --noconsole --icon=logo.ico client.py
```



