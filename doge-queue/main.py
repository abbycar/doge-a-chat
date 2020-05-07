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

import hashlib
import hmac
import json

from google.cloud import pubsub_v1

publisher_client = pubsub_v1.PublisherClient()

project_id = "<PROJECT_ID>"
topic_name = "<PUBSUB_TOPIC_NAME>"
topic_path = publisher_client.topic_path(project_id, topic_name)

futures = dict()

with open("config.json", "r") as f:
    data = f.read()
config = json.loads(data)

# Python 3+ version of https://github.com/slackapi/python-slack-events-api/blob/master/slackeventsapi/server.py
def verify_signature(request):
    """ Takes a Slack request and determines
    if the request and its credentials are valid.
    Args:
        request (flask.Request): A Slack request
    """

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    req = str.encode("v0:{}:".format(timestamp)) + request.get_data()
    request_digest = hmac.new(
        str.encode(config["SLACK_SECRET"]), req, hashlib.sha256
    ).hexdigest()
    request_hash = "v0={}".format(request_digest)

    if not hmac.compare_digest(request_hash, signature):
        raise ValueError("Invalid request/credentials.")


def doge_queue(request):
    """HTTP Cloud Function. Takes a Slack request and passes it to
    a second Cloud Function for processing via Pub/Sub.
    Args:
        request (flask.Request): A Slack request
    Returns:
        A response to the slack channel
    """

    if request.method != "POST":
        return "Only POST requests are accepted", 405

    verify_signature(request)
    data = json.dumps(request.form)

    futures.update({data: None})

    # When you publish a message, the client returns a future.
    future = publisher_client.publish(
        topic_path, data=data.encode("utf-8")  # data must be a bytestring.
    )

    """
    Check if future.result() resolved with the ID of the message.
    This indicates the message was successful.
    """
    try:
        print(future.result())
    except Exception as e:
        print("Error publishing: " + str(e))

    return "Working on it! 🐕"
