# doge-a-chat: A Slackbot that dogefies images 

This is a Slack slash command chatbot written in Python that takes an image URL and [dogefies](https://en.wikipedia.org/wiki/Doge_(meme)) it using [Cloud Functions](https://cloud.google.com/functions/docs), [Cloud Pub/Sub](https://cloud.google.com/pubsub/docs/), and [Cloud Vision](https://cloud.google.com/vision/docs). All images are saved in [Cloud Storage](https://cloud.google.com/storage/docs). **This is not an official Google product**.


For example, the app takes this image:

![doge og](https://i.kym-cdn.com/entries/icons/original/000/013/564/doge.jpg)

And returns this image:

![doge dogeified](https://storage.googleapis.com/dogeify-storage/20200501-185355)




## How it works

To kick off the process, a user enter the `/doge` command followed by the image URL they want to dogeify in a Slack channel.

![doge slash](https://drive.google.com/uc?export=view&id=1AmfMz04TXtxppWoJN1YDv37CJHJ7Hq-B)


The functionality of this app is broken down into two Cloud Functions.

### doge-queue
Triggered by HTTP requests from the Slackbot. 

Upon verifying the Slack equest, the function sends a message to Pub/Sub that contains the
request data. The function returns a message back to the Slack channel in the meantime.

![doge-a-chat working on it message!](https://drive.google.com/uc?export=view&id=1SB0mFpHhkvw1haaFsVUs2clLX5DOAef8)

### doge-response
Triggered when a message is published to a specified Pub/Sub topic.
 
After `doge-queue` publishes
its message to the Pub/Sub topic, `doge-response` opens the message to get the image URL. The image is run through Cloud Vision
to get the [labels](https://cloud.google.com/vision/docs/labels) associated with the image. 

[Pillow](https://pillow.readthedocs.io/en/stable/) dogeifies the image using the labels as overlay text.
   
The image is uploaded to Cloud Storage and sent back to the Slack channel as a message.

![doge response](https://drive.google.com/uc?export=view&id=1uBCAvXMbRdHSxMm73VxsMV_6EEoXDVL2)