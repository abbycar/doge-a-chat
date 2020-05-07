# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import requests
import json


from google.cloud import vision
from google.cloud import pubsub_v1
from PIL import Image, ImageDraw, ImageFont
from google.cloud import storage

import base64


storage_client = storage.Client()
vision_client = vision.ImageAnnotatorClient()
bucket = storage_client.bucket("dogeify-storage")


class DogeException(Exception):
    pass


class LargeImageException(DogeException):
    pass


class SmallImageException(DogeException):
    pass


class ImageURLException(DogeException):
    pass


class NoLabelsException(DogeException):
    pass


def send_message(timestamp, response_url):
    """ Sends a formatted message back to the Slack channel containing
    the dogefied image.
    Args:
        timestamp (string): The current time in the format yyyymmdd-hhmmss
        response_url (string): The URL location where the Slack interaction occurred.
    """
    message = {
        "response_type": "in_channel",
        "text": "Your dogeified image is at: https://storage.googleapis.com/dogeify-storage/"
        + timestamp,
    }
    requests.post(
        response_url, json=message, headers={"Content-type": "application/json"}
    )


def get_labels(request):
    """ Gets the Cloud Vision labels of an image from a URL.
    Args:
        request (object): An object representing a Slack request.
    Returns:
        A list of labels descriptions.
    """

    image = vision.types.Image()

    # Get image for processing by URI sent to slackbot
    image.source.image_uri = request["text"]
    response = vision_client.label_detection(image=image, max_results=6)

    # Catch if Cloud Vision returns empty annotations response
    if len(response.label_annotations) < 0:
        raise NoLabelsException("No labels generated")

    # Return Vision results from index 1 through 5. Ommiting first result to make labels more doge.
    # Remove any labels that are greater than 10 characters due to spacing
    return [
        annotation.description
        for annotation in response.label_annotations
        if len(annotation.description) <= 10
    ]


def dogeify_image(labels, request):
    """ Dogeifies an image at a URL and saves it to local storage.
    Args:
        labels (list): The labels generated from running the image against Cloud Vision.
        request (object): An object representing a Slack request.
    """

    try:
        response = requests.get(request["text"], stream=True)
    except:
        raise ImageURLException("Invalid image URL")

    response.raw.decode_content = True
    image = Image.open(response.raw)  # Open Slack request image for processing

    image_width, image_height = image.size

    # If image dimensions invalid, raise error
    if image_width < 400 or image_height < 400:
        raise SmallImageException("Image size too small")

    if image_width > 4000 or image_height > 4000:
        raise LargeImageException("Image too large")

    draw = ImageDraw.Draw(image)

    # Set font size to just under 10% of height
    font_size = image_height // 15

    # Set font to starting size
    font = ImageFont.truetype("COMIC.TTF", font_size)

    # If text width of longest label is greater than 1/5 of image width, decrease size
    while font.getsize(max(labels, key=len))[0] > image_width // 4:
        font_size -= 1
        font = ImageFont.truetype("COMIC.TTF", font_size)

    # Create custom strings and overlay them on image
    if len(labels) > 0:
        # "Such A"
        message = "Such " + labels[0].lower()
        (x, y) = (image_width // 15, image_height // 15)
        color = "rgb(255, 255, 255)"
        draw.text((x, y), message, fill=color, font=font)

    if len(labels) > 1:
        # "Is this B?"
        message = "Is this " + labels[1].lower() + "?"
        (x, y) = (
            image_width - font.getsize(message)[0] - image_height // 15,
            image_height // 15 * 3,
        )
        color = "rgb(255, 98, 98)"
        draw.text((x, y), message, fill=color, font=font)

    if len(labels) > 2:
        # "Much C"
        (x, y) = (image_width // 15 * 1.5, image_height // 15 * 6)
        message = "Much " + labels[2].lower()
        color = "rgb(255,105,180)"
        draw.text((x, y), message, fill=color, font=font)

    if len(labels) > 3:
        # "Wow so D"
        message = "Wow so " + labels[3].lower()
        (x, y) = (
            image_width // 2 - (font.getsize(message)[0] // 2),
            image_height // 15 * 12,
        )
        color = "rgb(152,251,152)"
        draw.text((x, y), message, fill=color, font=font)

    if len(labels) > 4:
        # "E"
        message = labels[4].lower()
        (x, y) = (
            image_width - font.getsize(message)[0] - (image_height // 15) * 3,
            image_height // 15 * 8,
        )
        color = "rgb(30,144,255)"
        draw.text((x, y), message, fill=color, font=font)
    image.save("/tmp/doge.png")


def upload_blob(timestamp):
    """ Uploads the dogefied image to Cloud Storage.
    Args:
        timestamp (string): The current time in the format yyyymmdd-hhmmss
    """
    blob = bucket.blob(timestamp)

    blob.upload_from_filename("/tmp/doge.png", content_type="image/png")
    os.unlink("/tmp/doge.png")  # Delete temp file


def doge_response(event, context):
    """ Background Cloud Function to be triggered by Pub/Sub.
    Takes the image URL passed in a Slack request and dogeifies it
    by overlaying text generated by Cloud Vision.
    Args:
        event (dict): The data associated with the Pub/Sub event.
        context (google.cloud.functions.Context): The metadata for the Cloud Function
    Returns:
        A response message to the slack channel containing the dogefied image.
    """

    timestr = time.strftime("%Y%m%d-%H%M%S")
    request = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    try:
        dogeify_image(get_labels(request), request)
    except DogeException as e:
        requests.post(
            request["response_url"],
            json={"text": "❌ " + str(e) + " ❌"},
            headers={"Content-type": "application/json"},
        )
        return

    upload_blob(timestr)
    return send_message(timestr, request["response_url"])
