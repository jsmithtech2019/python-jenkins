# IMPORTS
import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import requests
from flask import Flask, request
import random

app = Flask(__name__)

# Get Environment Variables
bot_id = os.environ.get('GROUPME_BOT_ID')
group_id = os.environ.get('GROUPME_GROUP_ID')
personal_token = os.environ.get('MY_GROUPME_TOKEN')

giphy_api_key = os.environ.get('GIPHY_API_KEY')
wolfram_api_key = os.environ.get('WOLFRAM_APP_ID')

class command:
    def __init__(self, name, syntax, description):
        self.name = name
        self.syntax = syntax
        self.description = description

commands = [
    command('helpCommand', '/help', 'Post help message.'),
    command('giphyCommand', '/giphy', 'Posts a relevant Gif.'),
    command('lmgtfyCommand', '/lmgtfy', 'Posts dumb question response.'),
    command('xkcdCommand', '/xkcd', 'Finds a relevant XKCD comic.'),
    command('gitCommit', '/commit', 'Posts a random git commit.'),
    command('clearCommand', '/clear', 'Clears the chat history.'),
    command('allCommand', '/all', 'Tags all members of the chat.'),

    # Easter Eggs
    #command('mitchEasterEgg', '/mitch', ''),
    #command('margEasterEgg', '/margs', '')

    # Disabled commands (paid api etc)
    #command('wolframCommand', '/wolf', 'Finds Answer on Wolfram Alpha.'),
    #command('redditCommand', '/reddit', 'Posts related Reddit comment.'),
]

# Confused Nick Young Face Image
confusedNickYoung = 'https://i.kym-cdn.com/entries/icons/mobile/000/018/489/nick-young-confused-face-300x256-nqlyaa.jpg'

# Mitch face
mitchFace = 'https://i.imgur.com/0HirwrK.jpg'

# Margarita image
margaritaImage = 'https://i.imgur.com/4SbhSbY.jpeg'

# Jenkins butlerish statements
butlerStatements = ['You rang sir?',
                    'Those who choose to be servants know the most about being free.',
                    'Am I really the only servant here?',
                    'You can\'t unfry an egg, sir.',
                    'Who employs butlers anymore?',
                    'I see nothing, I hear nothing, I only serve.',
                    'Good evening, Colonel. Can I give you a lift?',
                    'You are not authorized to access this area.',
                    'As far as I\'m concerned, \'whom\' is a word that was invented to make everyone sound like a butler.',
                    'Ah, the patter of little feet around the house. There\'s nothing like having a midget for a butler.',
                    'Wives in their husbands\' absences grow subtler, And daughters sometimes run off with the butler.',
                    'I think I\'d take a human butler over a robot one.',
                    'I went back-to-back from \'AI\' to \'Butler,\' literally with no break.',
                    'I\'m simply one hell of a butler.',
                    'It was no time for mercy, it was time to terminate with extreme prejudice.',
                    'The thing about a diversion is that it has to be diverting.',
                    'Jenkins, of course, is a gentleman’s gentlemen, not a butler, but if the call comes, he can buttle with the best of them.',
                    'There are few greater pleasures in life than a devoted butler.',
                    'A good butler should save his employer\'s life at least once a day.',
                    'Never pass up new experiences, they enrich the mind.',
                    'No one is a hero to their butler.',
                    'Very good, Sir',
                    'That\'s the sort of special touch that a butler always adds']



# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
    # 'message' is an object that represents a single GroupMe message.
    message = request.get_json()

    # Don't respond to bot messages
    if sender_is_bot(message):
        return 'Bot message, ignoring', 200

    # Convert text to lowercase
    message['text'] = message['text'].lower()

    # Mitch easter egg
    if '/mitch' in message['text'][0:len('/mitch')]:
        reply_with_image('',mitchFace)
        return '', 200

    # Margarita eater egg
    if 'marg' in message['text']:
        reply_with_image('',margaritaImage)
        return '', 200

    # Jenkins response
    if 'jenkin' in message['text']:
        reply(random.choice(butlerStatements))
        return '', 200

    # TODO: remove 
    if 'help' in message['text']:
        help()
        return '', 200

    return '', 200

################################################################################

# Print the help message
def help(comm='everything'):
    txt = ''
    for i in commands:
        txt += i.syntax + ': ' + i.description + '\n'

    reply(txt)


# Send a message in the groupchat
def reply(msg):
    url = 'https://api.groupme.com/v3/bots/post'
    data = {
        'bot_id'        : bot_id,
        'text'            : msg
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

# Send a message with an image attached in the groupchat
def reply_with_image(msg, imgURL):
    url = 'https://api.groupme.com/v3/bots/post'
    urlOnGroupMeService = upload_image_to_groupme(imgURL)
    data = {
        'bot_id'        : bot_id,
        'text'            : msg,
        'picture_url'        : urlOnGroupMeService
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

# Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(imgURL):
    imgRequest = requests.get(imgURL, stream=True)
    filename = 'temp.png'
    postImage = None
    if imgRequest.status_code == 200:
        # Save Image
        with open(filename, 'wb') as image:
            for chunk in imgRequest:
                image.write(chunk)
        # Send Image
        headers = {'content-type': 'application/json'}
        url = 'https://image.groupme.com/pictures'
        files = {'file': open(filename, 'rb')}
        payload = {'access_token': personal_token}
        r = requests.post(url, files=files, params=payload)
        imageurl = r.json()['payload']['url']
        os.remove(filename)
        return imageurl

# Checks whether the message sender is a bot
def sender_is_bot(message):
    return message['sender_type'] == "bot"
