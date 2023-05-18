import requests, os, time, jwt, json, boto3
from dotenv import load_dotenv

load_dotenv()


# Авторизуемся в Yandex Cloud и получаем IAM_TOKEN, return IAM_TOKEN
def auth_iam_token():
    with open('authorized_key.json') as f:
        file_content = f.read()
        templates = json.loads(file_content)
        private_key = templates['private_key']

    now = int(time.time())

    payload = {
        'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        'iss': os.getenv('service_account_id'),
        'iat': now,
        'exp': now + 360}

    # Формирование JWT
    encode_token = jwt.encode(
        payload,
        private_key,
        algorithm='PS256',
        headers={'kid': os.getenv('key_id')})

    url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
    params = {'jwt': encode_token}
    HEADERS = {'Content-Type': 'application/json'}

    req = requests.post(url, headers=HEADERS, json=params)
    IAM_TOKEN = json.loads(req.content)['iamToken']

    return IAM_TOKEN


# Получаем access_key AWS с помощью IAM-токена, return aws_access_key_id, aws_secret_access_key
# aws_access_key_id, aws_secret_access_key получаем один раз и сохраняем, они не имеют срока действия
def auth_access_key(IAM_TOKEN):
    url_access_key = 'https://iam.api.cloud.yandex.net/iam/aws-compatibility/v1/accessKeys'
    params_access_key = {
        "serviceAccountId": f"{os.getenv('service_account_id')}",
        "description": "access key for storage",
    }
    headers_access_key = {'Content-Type': 'application/json',
                          "Authorization": f"Bearer {IAM_TOKEN}"}

    req_access_key = requests.post(url_access_key, headers=headers_access_key, json=params_access_key)
    data = req_access_key

    aws_access_key_id = json.loads(data.content)['accessKey']['keyId']
    aws_secret_access_key = json.loads(data.content)['secret']

    return aws_access_key_id, aws_secret_access_key


# Создаем сессию AWS s3
def s3_session():
    session_boto = boto3.Session(
        aws_access_key_id=os.getenv('aws_access_key_id'),
        aws_secret_access_key=os.getenv('aws_secret_access_key'),
    )

    s3 = session_boto.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        region_name='ru-central1',
    )

    return s3


# Загружаем аудиофайл в облако Яндекс, return filelink
def yandex_uploadfile(file, s3):
    with open(f"{file}", "rb") as f:
       s3.upload_fileobj(f, os.getenv('bucket'), f"{file}")

    filelink = f"https://storage.yandexcloud.net/{os.getenv('bucket')}/{file}"

    return filelink


# Получаем авторизацию в Yandex Speechkit и передаем сохраненный объект для распознавания речи, return text
def auth_speechkit(filelink, IAM_TOKEN):
    POST = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"
    body = {
        "config": {
            "specification": {
                "languageCode": "ru-RU",
                "literature_text": True,
            }
        },
        "audio": {
            "uri": filelink
        }
    }

    header = {'Content-Type': 'application/json',
              "Authorization": f"Bearer {IAM_TOKEN}"}

    # Отправить запрос на распознавание.
    req = requests.post(POST, headers=header, json=body)
    id = json.loads(req.content)['id']

    # Запрашивать на сервере статус операции, пока распознавание не будет завершено.
    while True:
        time.sleep(3)

        GET = "https://operation.api.cloud.yandex.net/operations/{id}"
        req = requests.get(GET.format(id=id), headers=header)
        req = req.json()

        if req['done']: break

    # Показать только текст из результатов распознавания.
    str_list = []

    for chunk in req['response']['chunks']:
        str_list.append(chunk['alternatives'][0]['text'])

    text = '\n'.join(str_list)

    return text


# Удаляем загруженный объект из хранилища, аргументом передаем название объекта (путь), return response
def delete_file(file, s3):
    # Удаляем ранее загруженный объект из хранилища
    response = s3.delete_object(
        Bucket=os.getenv('bucket'),
        Key=file
        )

    return response

