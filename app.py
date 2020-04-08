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

# Contains the function name, command syntax and description
# of the each available command
class command:
    def __init__(self, name, syntax, description):
        self.name = name
        self.syntax = syntax
        self.description = description

# Command objects list
commands = [
    command('help', '/help', 'Post help message.'),
    command('giphy', '/giphy', 'Posts a relevant Gif.'),
    command('lmgtfy', '/lmgtfy', 'Posts dumb question response.'),
    command('xkcd', '/xkcd', 'Finds a relevant XKCD comic.'),
    command('git', '/commit', 'Posts a random git commit.'),
    command('clear', '/clear', 'Clears the chat history.'),
    command('all', '/all', 'Tags all members of the chat.'),

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

    # Check if any command is being called by user
    for c in commands:
        if c.syntax in message['text'][0:len(c.syntax)]:
            # Call the method with that name
            # globals()
            # print('Fnc name: ' + c.name)
            # print('Message: ' + message['text'])
            globals()[c.name](message['text'])
            return '', 200

    # No command called or found, return
    return '', 200

################################################################################

# Print the help message for all commands
def help(unused):
    txt = 'Usage instructions for your Butler:\n'
    for i in commands:
        txt += '"{}" - {}\n'.format(i.syntax, i.description)

    reply(txt)

# Post a relevant gif from Giphy
def giphy(text):
    print('Text: ' + text)
    search = encodeQuery(text[len('/giphy '):])
    print('Search: ' + search)
    imgURL = 'https://api.giphy.com/v1/gifs/search?api_key={}&q={}'.format(giphy_api_key, search)

    print('url: ' + imgURL)
    try:
        # Get Gif from Giphy
        imgRequest = requests.get(imgURL, stream=True)

        print('Content: ' + imgRequest.content)
        print('Data: ' + json.parse(imgRequest.content))['data']
        # Parse gif
        jsobj = json.parse(imgRequest.content)['data'][0]

        # Format and respond with URL
        giphyUrl = 'http://i.giphy.com/{}.gif'.format(jsobj['id'])
        reply_with_image(giphyUrl)
    except Exception as e:
        # If no gif was returned, respond as such
        print('Exception: ' + e)
        reply('Couldn\'t find a gif 💩')

def lmgtfy(text):
    reply('lmgtfy')

def xkcd(text):
    reply('xkcd')

def git(unused):
    reply('git')

def clear(unused):
    reply('clear')

def all(unused):
    reply('all')

# Removes spaces and replaces them with '+' marks
def encodeQuery(query):
    return query.replace(' ','+')

# Send a message in the groupchat
def reply(msg):
    url = 'https://api.groupme.com/v3/bots/post'
    data = {
        'bot_id': bot_id,
        'text': msg
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

# Send a message with an image attached in the groupchat
def reply_with_image(msg, imgURL):
    url = 'https://api.groupme.com/v3/bots/post'
    urlOnGroupMeService = upload_image_to_groupme(imgURL)
    data = {
        'bot_id': bot_id,
        'text': msg,
        'picture_url': urlOnGroupMeService
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

# Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(imgURL):
    if 'gif' in imgURL or 'giph' in imgURL:
        filename = 'temp.gif'
    else:
        filename = 'temp.png'
    postImage = None

    imgRequest = requests.get(imgURL, stream=True)

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
