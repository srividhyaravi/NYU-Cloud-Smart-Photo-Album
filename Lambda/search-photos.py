import json
import boto3
import requests
#from botocore.vendored import requests

AMAZON_LEX_BOT = "photobot_test"
LEX_BOT_ALIAS = "test_one"
USER_ID = "user"


TABLENAME = 'photos'
ELASTIC_SEARCH_URL = "https://search-photos-tsplel4joanuc5gkqwjv3htvyu.us-east-1.es.amazonaws.com/_search?q="
#ELASTIC_SEARCH_URL = "https://search-photos-tsplel4joanuc5gkqwjv3htvyu.us-east-1.es.amazonaws.com/_search?q="
# ELASTIC_SEARCH_URL = "https://search-photos1-df7kaxqciee65thyvk6f6wh64i.us-east-1.es.amazonaws.com/_search?q="

# S3_URL = "https://cloud9223-photo-album.s3.amazonaws.com/"
S3_URL = "https://photo-store-b2.s3.amazonaws.com/"

def post_on_lex(query, user_id=USER_ID):
    """
    Get the user input from the frontend as text and pass
    it to lex. Lex will generate a new response.
    it will return a json response: 
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lex-runtime.html
    """
    client = boto3.client('lex-runtime')
    lex_response = client.post_text(botName=AMAZON_LEX_BOT,
                                    botAlias=LEX_BOT_ALIAS,
                                    userId=user_id, 
                                    inputText=query)
    
    print("lex-response", lex_response)
    
    if lex_response['slots']['Label_one'] and lex_response['slots']['Label_two']:
        labels = 'labels:' + lex_response['slots']['Label_one'] + '+' + 'labels:' + lex_response['slots']['Label_two']
    elif lex_response['slots']['Label_one']:
        labels = 'labels:' + lex_response['slots']['Label_one']
    else:
        return
    return labels


def get_photos_ids(URL, labels):
    """
    return photos ids having the 
    labels as desired 
    """
    
    URL = URL + str(labels)
    #response = requests.get(URL, auth=awsauth).content
    response = requests.get(URL, auth=("roshnisen","#Cloudtest123")).content
    print("Response: ",response)
    data = json.loads(response)
    hits = data["hits"]["hits"]
    id_list = []
    labels_list = []
    for result in hits:
        _id = result["_source"]["objectKey"]
        id_list.append(_id)
        _labels = result["_source"]["labels"]
        labels_list.append(_labels)
    return id_list, labels_list


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin":"*",
            "Access-Control-Allow-Credentials" : True,
        },
    }

# def convert_speechtotext():

#     transcribe = boto3.client('transcribe')

#     job_name = datetime.datetime.now().strftime("%m-%d-%y-%H-%M%S")
#     job_uri = "https://awstranscribe-recordings.s3.amazonaws.com/Recording.wav"
#     storage_uri = "awstranscribe-output"

#     s3 = boto3.client('s3')
#     transcribe.start_transcription_job(
#         TranscriptionJobName=job_name,
#         Media={'MediaFileUri': job_uri},
#         MediaFormat='wav',
#         LanguageCode='en-US',
#         OutputBucketName=storage_uri
#     )

#     while True:
#         status = transcribe.get_transcription_job(
#             TranscriptionJobName=job_name)
#         if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
#             break
#         time.sleep(5)

#     print("Transcript URL: ", status)

#     job_name = str(job_name) + '.json'
#     print(job_name)
#     obj = s3.get_object(Bucket="awstranscribe-output", Key=job_name)
#     print("Object : ", obj)
#     body = json.loads(obj['Body'].read().decode('utf-8'))
#     print("Body :", body)

#     return body["results"]["transcripts"][0]["transcript"]



def lambda_handler(event, context):
    
    query = event['queryStringParameters']['q']
    #query = "Show me dog"
    # if(query == "searchAudio"):
    #     query = convert_speechtotext()
    
    labels = post_on_lex(query)
    id_list, labels_list = get_photos_ids(ELASTIC_SEARCH_URL, labels)
    
    results = []
    for i, l in zip(id_list, labels_list):
        results.append({"url": S3_URL + i, "labels": l})
    
    print(results)
    response = {"results": results}    
    return respond(None, response)

