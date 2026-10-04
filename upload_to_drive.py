import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Требуемые права доступа только на запись/управление файлами на Диске
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def upload_file(file_path, file_name):
    creds = None
    # token.json сохраняет токен авторизации после первого входа
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Метаданные файла на Диске
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)

    # Загрузка файла в облако
    file = service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id, webViewLink'
    ).execute()

    print(f"Файл успешно загружен!")
    print(f"ID файла в Google Drive: {file.get('id')}")
    print(f"Ссылка для просмотра: {file.get('webViewLink')}")

if __name__ == '__main__':
    target_file = "Rabochaya_programma_Pravo_Full_Name_10_klass.docx"
    upload_file(target_file, target_file)
