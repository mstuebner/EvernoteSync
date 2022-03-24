"""
Personal kann:
- Notizen, Notizbücher und Schlagwörter erstellen
- Notizen, Notizbücher und Schlagwörter aktualisieren
- Notizbücher und Schlagwörter auflisten
- Notizen laden

Personal kann NICHT:
- Notizbücher und Schlagwörter löschen
- Kontoinformationen abrufen
- Notizen endgültig löschen
- Informationen des Benutzerkontos aktualisieren
"""

from evernote.api.client import EvernoteClient


prod_token = ''

client = EvernoteClient(token=prod_token, sandbox=False)
userStore = client.get_user_store()
user = userStore.getUser()
print(user.username)
print('pass')