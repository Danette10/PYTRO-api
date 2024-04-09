# PYTRO

<p align="center">
  <img src="logo.png" alt="PYTRO logo"/>
</p>

## Documentation

- [📚 http://127.0.0.1:5000/](http://127.0.0.1:5000)

# Summary
- [⚠️ DISCLAIMER ⚠️](#-disclaimer-)
- [Installation](#installation)
- [Flask-Migrate](#flask-migrate)
  - [Initialization of Flask-Migrate](#initialization-of-flask-migrate)
  - [Migration](#migration)

# ⚠️ DISCLAIMER ⚠️
This project is developed for educational purposes only. The aim is to understand and demonstrate the security risks associated with RAT (Remote Access Trojan) software and to encourage the development of effective countermeasures. The author(s) of this project do not endorse any malicious use of the materials provided.

By using or interacting with this software in any way, you agree to use it solely for educational, ethical hacking, and security research purposes. It is strictly forbidden to use the software for illegal activities, and the author(s) will not be responsible for any misuse of the software.

All users are encouraged to report any vulnerabilities or security issues found within this software to the author(s) for improvement. Remember, unauthorized access to computer systems is illegal and punishable by law. Always conduct your security research within legal boundaries and with proper authorization.

Use this software at your own risk.

# Installation
```bash
pip install -r requirements.txt
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



