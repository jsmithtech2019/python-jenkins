# IMPORTS
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import json
import os
import random
import requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen

app = Flask(__name__)

# Database Information
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)

class ImagesTable(db.Model):
    __tablename__ = "images"

    _id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    url = db.Column(db.String(200), nullable = False)

    def __init__(self, url):
        self.url = url

class PostedImagesTable(db.Model):
    __tablename__ = "posted_images"

    _id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    url = db.Column(db.String(200), nullable = False)

    def __init__(self, url):
        self.url = url

# Get Environment Variables
bot_id = os.environ.get('GROUPME_BOT_ID')
group_id = os.environ.get('GROUPME_GROUP_ID')
personal_token = os.environ.get('MY_GROUPME_TOKEN')

giphy_api_key = os.environ.get('GIPHY_API_KEY')
wolfram_api_key = os.environ.get('WOLFRAM_APP_ID')
dictionary_api_key = os.environ.get('DICTIONARY_API_KEY')
thesaurus_api_key = os.environ.get('THESAURUS_API_KEY')

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
    command('dictionary', '/dict', 'Returns definition of word.'),
    command('thesaurus', '/thes', 'Returns similar words.'),
    command('wolframCommand', '/wolf', 'Finds Answer on Wolfram Alpha.'),
    command('sauce', '/sauce', 'Returns URL of the last image.'),
    command('origin', '/origin', 'Returns origin URL of image.')

    # Disabled commands (paid api etc)
    #command('redditCommand', '/reddit', 'Posts related Reddit comment.'),
]

# Automatic responses to various strings within a message
auto = {
    'mitch': 'https://i.imgur.com/0HirwrK.jpg',
    'marg': 'https://i.imgur.com/4SbhSbY.jpeg',
    'wut': 'https://i.kym-cdn.com/entries/icons/mobile/000/018/489/nick-young-confused-face-300x256-nqlyaa.jpg',
    'sniper': 'https://thumbs.gfycat.com/FirmExcitableEyas-small.gif',
    'porque no los dos': 'https://thumbs.gfycat.com/FirmExcitableEyas-small.gif',
    'wat ': 'https://i.imgur.com/qMKXZKh.gif'
}

# Load Jenkins butlerish statements and return one at random
def getButlerQuote():
    with open('butler_statments.json', 'r') as f:
        return random.choice(json.loads(f.read()))

# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
    # 'message' is an object that represents a single GroupMe message.
    message = request.get_json()

    try:
        print(message)
    except Exception as e:
        print('Exception: ' + e)

    # Don't respond to bot messages
    if sender_is_bot(message):
        return 'Bot message, ignoring', 200

    # Log message text (again)
    try:
        print('Message text: ' + message['text'])
    except Exception as e:
        print('Exception: ' + e)
    
    # Convert text to lowercase
    message['text'] = message['text'].lower()

    # Check if any command is being called by user
    for c in commands:
        if c.syntax in message['text'][0:len(c.syntax)]:
            # Call the method with that name
            globals()[c.name](message['text'])
            return '', 200

    # Reply with one of the automatic easter eggs
    for a in auto:
        if a in message['text']:
            reply_with_image('',auto[a])
            return '', 200

    # Jenkins response
    if 'jenkin' in message['text']:
        reply(random.choice(getButlerQuote()))
        return '', 200

    # Check if someone was removed or added
    try:
        if (message['sender_type'] == 'system') and ('removed' in message['text']):
            print('Sniping...')
            giphy('/giphy sniper')
            return '', 200
        elif (message['sender_type'] == 'system') and ('added' in message['text']):
            giphy('/giphy hello')
            return '', 200
    except:
        pass

    # No command called or found, return
    return 'No command found', 200

################################################################################

# Print the help message for all commands
def help(unused):
    txt = 'Usage instructions for your Butler:\n'
    for i in commands:
        txt += '"{}" - {}\n'.format(i.syntax, i.description)

    reply(txt)

# Find the first place an image was posted
def origin(json_obj):
    try:
        imgUrl = json_obj['attachments'][0]['url']
        # Hit reverse image api
        # Parse response for origin URL
        # Reply with origin
    except Exception as e:
        print('Exception: ' + e)
        reply('No image origin found.')

# Reply with URL of last posted image
def sauce(unused):
    last_image_url = ImagesTable.query.order_by(ImagesTable._id.desc()).first().url
    reply('The last image posted was from:\n' + last_image_url)

# Query Wolfram Alpha API with question
def wolframCommand(text):
    data = {
        'appid': wolfram_api_key,
        'input': text[len('/wolf '):],
        'output': 'json'
    }
    url = "http://api.wolframalpha.com/v2/query?" + urlencode(data)
    resp = json.loads(urlopen(url).read().decode())

    try:
        reply('The answer is: ' + resp['queryresult']['pods'][1]['subpods'][0]['plaintext'])
    except:
        reply('No solution could be found')

# Post a relevant gif from Giphy
def giphy(text):
    data = {
        'api_key': giphy_api_key,
        'q': text[len('/giphy '):],
        'limit': 1
    }
    url = 'https://api.giphy.com/v1/gifs/search?' + urlencode(data)

    # Get gif from Giphy
    imgRequest = urlopen(url).read().decode()

    try:
        # Parse gif response
        idobj = json.loads(imgRequest)['data'][0]

        # Format and respond with URL
        giphyUrl = 'http://i.giphy.com/{}.gif'.format(idobj['id'])
        reply_with_image('', giphyUrl)

    except Exception as e:
        # If no gif was returned, respond as such
        print('Exception: ' + str(e))
        reply('Couldn\'t find a gif 💩')

def lmgtfy(text):
    data = {
        'q': text[len('/lmgtfy '):]
    }
    reply('http://lmgtfy.com/?' + urlencode(data))

def xkcd(text):
    data = {
        'action': 'xkcd',
        'query': text[len('/xkcd '):]
    }
    url = 'https://relevantxkcd.appspot.com/process?' + urlencode(data)

    try:
        # response
        comicRequest = urlopen(url).read().decode()

        # Get comic file name
        comicName = comicRequest.split()[3].split('/')[-1]

        reply_with_image('','https://imgs.xkcd.com/comics/{}'.format(comicName))

    except Exception:
        reply('Couldn\'t find an XKCD 💩')

# Get a random git commit message
def git(unused):
    url = 'http://www.whatthecommit.com/index.txt'
    reply(urlopen(url).read().decode())

# Clear the chat screen by posting newlines
def clear(unused):
    # What a silly command
    reply(' \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nChat cleared.')

# Tag everyone in the chat
def all(unused):
    url = 'https://api.groupme.com/v3/groups/{}?token={}'.format(group_id,personal_token)

    groupInfo = json.loads(urlopen(url).read().decode())['response']

    text = '{"bot_id":"' + bot_id + '","text":"@all","attachments":[{'
    loci = '"loci":['
    user_ids = '],"type":"mentions","user_ids":['
    for person in groupInfo['members']:
        loci += '[0,1],'
        user_ids += '"{}",'.format(person['user_id'])

    text += loci[:-1] + user_ids[:-1] + ']}]}'

    # Post to Groupme
    req = Request('https://api.groupme.com/v3/bots/post')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsonData = text.encode('utf-8')
    req.add_header('Content-Length', len(jsonData))
    urlopen(req, jsonData)

# Find the dictionary definition of a word
def dictionary(text):
    data = {
        'key': dictionary_api_key
    }
    url = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{}?'.format(text[len('/dict '):].partition(' ')[0]) + urlencode(data)
    #url = 'https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key={}'.format(text[len('/dict '):].partition(' ')[0],dictionary_api_key)

    try:
        # response
        resp = 'Definition: ' + '; '.join(json.loads(urlopen(url).read().decode())[0]['shortdef'])

        reply(resp)

    except Exception:
        reply('Couldn\'t find a definition.')

# Find the similar words using thesaurus
def thesaurus(text):
    url = 'https://dictionaryapi.com/api/v3/references/thesaurus/json/{}?key={}'.format(text[len('/thes '):].partition(' ')[0],thesaurus_api_key)

    try:
        # response
        resp = '; '.join(json.loads(urlopen(url).read().decode())[0]['shortdef'])

        reply(resp)

    except Exception:
        reply('Couldn\'t find a definition.')

# Send a message in the groupchat
def reply(msg):
    url = 'https://api.groupme.com/v3/bots/post'
    data = {
        'bot_id': bot_id,
        'text': msg
    }
    request = Request(url, urlencode(data).encode())
    urlopen(request).read().decode()

# Send a message with an image attached in the groupchat
def reply_with_image(msg, imgURL):
    # Store copy of original URL
    new_data = ImagesTable(imgURL)
    db.session.add(new_data)
    db.session.commit()

    # Upload to GroupMe for processing
    url = 'https://api.groupme.com/v3/bots/post'
    urlOnGroupMeService = upload_image_to_groupme(imgURL)
    data = {
        'bot_id': bot_id,
        'text': msg,
        'picture_url': urlOnGroupMeService
    }
    request = Request(url, urlencode(data).encode())
    urlopen(request).read().decode()

# Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(imgURL):
    if 'gif' in imgURL or 'giph' in imgURL:
        filename = 'temp.gif'
    else:
        filename = 'temp.png'

    imgRequest = requests.get(imgURL, stream=True)

    if imgRequest.status_code == 200:
        # Save Image
        with open(filename, 'wb') as image:
            for chunk in imgRequest:
                image.write(chunk)

        # Send Image
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
