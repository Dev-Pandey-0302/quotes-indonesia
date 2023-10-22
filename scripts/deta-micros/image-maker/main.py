# quotes format: {caption}. --{author}
# example: `Lorem ipsum dolor sit. --Amet`

import json
import os
import random
from deta import Deta
from dotenv import load_dotenv
from flask import Flask, request, send_file
from io import BytesIO
from urllib import request as libreq
from PIL import Image, ImageDraw, ImageFont
from urllib.error import URLError

load_dotenv('env')

app = Flask(__name)
deta = Deta(os.environ.get('PROJECT_KEY'))

font_url = 'https://github.com/google/fonts/blob/main/ofl/neucha/Neucha.ttf?raw=true'
quote_api_url = os.environ.get('QUOTE_API_URL')
random_quote_url = quote_api_url + '/random'

def generate_image(quote_body, quote_by):
    try:
        # Image configuration
        img_width = 612
        img_height = 612

        # Font configuration
        font_urls = [font_url]
        font_selected = random.choice(font_urls)
        font_get = libreq.urlopen(font_selected)
        font = ImageFont.truetype(BytesIO(font_get.read()), 35)

        # Color configuration
        colors = [{'bg': (255, 255, 255), 'fg': (100, 100, 100)}]
        color = random.choice(colors)

        # Draw image
        image = Image.new('RGB', (img_width, img_height), color=color['bg'])
        document = ImageDraw.Draw(image)

        # Find the average size of the letter in quote_body
        sum = 0
        for letter in quote_body:
            sum += document.textsize(letter, font=font)[0]
        average_length_of_letter = sum / len(quote_body)

        # Find the number of letters to be put on each line
        number_of_letters_for_each_line = (img_width / 1.818) / average_length_of_letter

        # Build new text to put on the image
        incrementer = 0
        fresh_quote = ''
        for letter in quote_body:
            if (letter == '-'):
                fresh_quote += '' + letter
            elif (incrementer < number_of_letters_for_each_line):
                fresh_quote += letter
            else:
                if(letter == ' '):
                    fresh_quote += '\n'
                    incrementer = 0
                else:
                    fresh_quote += letter
            incrementer += 1
        fresh_quote += '\n\n--' + quote_by

        # Render the text in the center of the box
        dim = document.textsize(fresh_quote, font=font)
        x2 = dim[0]
        y2 = dim[1]
        qx = (img_width / 2 - x2 / 2)
        qy = (img_height / 2 - y2 / 2)
        document.text((qx, qy), fresh_quote, align="center", font=font, fill=color['fg'])

        # Save image and return it as a response
        image_io = BytesIO()
        image.save(image_io, 'JPEG', quality=100)
        image_io.seek(0)

        return send_file(image_io, mimetype='image/jpeg')
    except Exception as e:
        return f"Error generating image: {str(e)}", 500  # Return an error response with status code 500

@app.get('/')
def http_index():
    try:
        default_quote = 'Aku masih menunggumu. --Lakuapik'
        quote_full = request.values.get('text') or default_quote
        quote_body, quote_by = quote_full.split(' --')
        return generate_image(quote_body, quote_by)
    except ValueError as e:
        return f"Invalid quote format: {str(e)}", 400  # Return a client error response with status code 400

@app.get('/random')
def http_random():
    try:
        result = libreq.urlopen(random_quote_url).read()
        data = json.loads(result)
        return generate_image(data.get('quote'), data.get('by'))
    except (URLError, json.JSONDecodeError) as e:
        return f"Error fetching and processing random quote: {str(e)}", 500  # Return an error response with status code 500

if __name__ == "__main__":
    app.run()
