# A-Math-Solving-Website
This repo contains part of the code for this website, excluding the config file for api key and email config, for a sample code viewing purpose.

This project:
- Written in Python with Flask and deployed on the Amazon Lambda, and EC2 recently.
- Fully responsive design based on Bootstrap.
- Allow users to sign up/in, upload a hand-written mathematics problemsand display the result and stored in his/her account.
- Email confirmation for registration by using regular libraries in python flask, not any cloud platform api (User must activate the confimation email to use functions provided by the website).
- A Question and Answer (Q&A) Community which allows users to post and answer question, select the best answer.(Use Jinja2 to write conditional logic to let different users see a different view of the same page)
- Customized CSS and Javascript(Some AngularJS) functions.
- Use DynamoDB as database, write function to access DynamoDB with boto3.
- Use S3 for file storage.
- For demo, please contact me.
