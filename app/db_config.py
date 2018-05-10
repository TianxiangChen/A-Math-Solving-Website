import boto3
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from dateutil import tz

# User table: username*, password, email
# Quesiton:   username, pic_url*, latex, soln_latex, time
# QandA: qaid*, question_title, question, author, question_time, best_ans_user
# QandA_Answers: qaid*, ans_time, ans_user*, answer
# counter: counter

# this is not a good approach but i need an auto-incremet qaid.
# thik as a temp solution for any kind of counter used in the db.

USER_TABLE_NAME = 'Users'
# QUESTION_TABLE_NAME = 'Questions'
Q_AND_A_TABLE_NAME = 'QandA'
Q_AND_A_ANSWERS_TABLE_NAME = 'QandA_Answers'
COUNTER_TABLE_NAME = 'counter'

db_config = {
    'username': 'ece1779',
    'password': 'secret',
    'host': 'localhost',
    'database': 'ece1779'
}

dynamo = boto3.resource('dynamodb')

user_table = dynamo.Table(USER_TABLE_NAME)
# question_table = dynamo.Table(QUESTION_TABLE_NAME)
qanda_table = dynamo.Table(Q_AND_A_TABLE_NAME)
qanda_answers_table = dynamo.Table(Q_AND_A_ANSWERS_TABLE_NAME)
counter_table = dynamo.Table(COUNTER_TABLE_NAME)

def get_toronto_time():
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Toronto')
    utctime = datetime.datetime.utcnow()
    utctime = utctime.replace(tzinfo=from_zone)
    toronto_time = utctime.astimezone(to_zone)
    temp =  toronto_time.replace(microsecond=0).isoformat()
    groups = temp.split('-')
    toronto_time = '-'.join(groups[:3])
    return toronto_time

def add_user(username, password, email):
    passwd_hash = generate_password_hash(password, salt_length=8)
    confirmed = False
    user_table.put_item(
        Item={
            'username': username,
            'password': passwd_hash,
            'confirmed': confirmed,  # this need to be implemented if email verification enabled
            'email': email,
            'qlist': []
        }
    )


def get_user(username):
    response = user_table.get_item(
        Key={
            'username': username
        }
    )

    return response.get('Item')


def get_user_by_email(email):
    response = user_table.scan(
        FilterExpression=Attr('email').eq(email)
    )

    return response.get('Items')


def set_user_email(username, email):
        user_table.update_item(
        Key={
            'username': username,
        },
        UpdateExpression='SET email = :s',
        ExpressionAttributeValues={
            ':s': email
        }
        )

def set_user_confirmed(username):
        user_table.update_item(
        Key={
            'username': username,
        },
        UpdateExpression='SET confirmed = :d',
        ExpressionAttributeValues={
            ':d': True
        }
        )


def user_check_confirmed(username):
    return get_user(username).get('confirmed')

def user_email(username):
    return get_user(username).get('email')


def user_authenticate(user, password_pt):
    """Use this function to authticate salted password.
    :param user: a user object returned from AWS
    :param password_pt: plain text password
    :return: true or false
    """
    return check_password_hash(user['password'], password_pt)



def create_question(username, question_url, input_latex, soln_latex):
    user_table.update_item(
        Key={
            'username': username
        },
        UpdateExpression="SET qlist = list_append(qlist, :i)",
        ExpressionAttributeValues={
            ':i': [{'pic_url': question_url,
                    'input_latex': input_latex,
                    'soln_latex': soln_latex,
                    'time': get_toronto_time()}],
        },
        ReturnValues="UPDATED_NEW"
    )


def get_user_question(username):
    return get_user(username).get('qlist')


# Q and A function
def get_all_qanda():
    response = qanda_table.scan()
    return response.get('Items')


def get_a_qanda(qaid):
    response = qanda_table.query(
        KeyConditionExpression=Key('qaid').eq(qaid)
    )
    result = response.get('Items')
    return result[0]


def create_qanda(question_title, question, author):
    counter = get_qanda_counter() + 1
    initial_best_ans_user = "not solved"
    qanda_table.put_item(
        Item={
            'qaid': counter,
            'question_title': question_title,
            'question': question,
            'author': author,
            'question_time': get_toronto_time(),
            'best_ans_user': initial_best_ans_user,
        }
    )
    increment_qanda_counter(counter)

def choose_best_answer(qaid, answer_user):
    qanda_table.update_item(
    Key={
        'qaid': qaid,
    },
    UpdateExpression='SET best_ans_user = :a',
    ExpressionAttributeValues={
        ':a': answer_user
        }
    )

# Q and A Answers function
def get_qanda_answers(qaid):
    response = qanda_answers_table.query(
        KeyConditionExpression=Key('qaid').eq(qaid)
    )
    return response.get('Items')

def answer_a_question(qaid, answer, answer_user):
    qanda_answers_table.put_item(
        Item={
            'qaid': qaid,
            'ans_time': get_toronto_time(),
            'ans_user': answer_user,
            'answer': answer,
        }
    )

# Q and A counter function
def reset_qanda_counter():
    # remove everything inside
    counter_table.delete_item(
    Key={
        'counter_name': 'qanda',
        }
    )

    counter_table.put_item(
        Item={
            'counter_name': 'qanda',
            'counts': 0,
        }
    )

def increment_qanda_counter(i):
        counter_table.update_item(
        Key={
            'counter_name': 'qanda',
        },
        UpdateExpression='SET counts = :n',
        ExpressionAttributeValues={
            ':n': i
        }
        )

def get_qanda_counter():
    response = counter_table.query(
        KeyConditionExpression=Key('counter_name').eq('qanda')
    )
    return int(response.get('Items')[0]['counts'])
    # return counter

def create_tables():
    utable = dynamo.create_table(
        TableName=USER_TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'username',
                'KeyType': 'HASH'  # Sort key
            },
            # {
            #     'AttributeName': 'email',
            #     'KeyType': 'RANGE'  # Sort key
            # }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            # {
            #     'AttributeName': 'email',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'password',
            #     'AttributeType': 'S'
            # },
            #     'AttributeName': 'confirmed',
            #     'AttributeType': 'BOOL'
            # },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    # qtable = dynamo.create_table(  # question table
    #     TableName=QUESTION_TABLE_NAME,
    #     KeySchema=[
    #         {
    #             'AttributeName': 'pic_url',
    #             'KeyType': 'HASH'  # Sort key
    #         },
    #         # {
    #         #     'AttributeName': 'time',
    #         #     'KeyType': 'RANGE'  # Sort key
    #         # }
    #     ],
    #     AttributeDefinitions=[
    #         {
    #             'AttributeName': 'pic_url',
    #             'AttributeType': 'S'
    #         },
    #         # {
    #         #     'AttributeName': 'time',
    #         #     'AttributeType': 'S'
    #         # },
    #         # {
    #         #     'AttributeName': 'username',
    #         #     'AttributeType': 'S'
    #         # },
    #         # {
    #         #     'AttributeName': 'latex',
    #         #     'AttributeType': 'S'
    #         # },
    #         # {
    #         #     'AttributeName': 'soln_latex',
    #         #     'AttributeType': 'S'
    #         # },
    #     ],
    #     ProvisionedThroughput={
    #         'ReadCapacityUnits': 10,
    #         'WriteCapacityUnits': 10
    #     }
    # )

    qatable = dynamo.create_table(  # question and answer table
        TableName=Q_AND_A_TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'qaid',
                'KeyType': 'HASH'  # Sort key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'qaid',
                'AttributeType': 'N'
            },
            # {
            #     'AttributeName': 'question_title',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'question',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'author',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'best_ans_user',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'question_time',
            #     'AttributeType': 'S'
            # },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    qaanswertable = dynamo.create_table(  # question and answer table
        TableName=Q_AND_A_ANSWERS_TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'qaid',
                'KeyType': 'HASH'  # Sort key
            },
            {
                'AttributeName': 'ans_user',
                'KeyType': 'RANGE'  # Range key
            },

        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'qaid',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'ans_user',
                'AttributeType': 'S'
            },
            # {
            #     'AttributeName': 'ans_time',
            #     'AttributeType': 'S'
            # },
            # {
            #     'AttributeName': 'answer',
            #     'AttributeType': 'S'
            # },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    countertable = dynamo.create_table(  # question table
        TableName=COUNTER_TABLE_NAME,
        KeySchema=[
            {
                'AttributeName': 'counter_name',
                'KeyType': 'HASH'  # Sort key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'counter_name',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    utable.meta.client.get_waiter('table_exists').wait(TableName='Users')
    # qtable.meta.client.get_waiter('table_exists').wait(TableName='Questions')
    qatable.meta.client.get_waiter('table_exists').wait(TableName='QandA')
    qaanswertable.meta.client.get_waiter('table_exists').wait(TableName='QandA_Answers')
    countertable.meta.client.get_waiter('table_exists').wait(TableName='Counter')
