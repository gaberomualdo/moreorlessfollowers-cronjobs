import instaloader, math, schedule, requests, smtplib, ssl, json
from bs4 import BeautifulSoup
from unidecode import unidecode
from time import sleep

config_dict = json.loads(open('config.json').read())
amount_of_accounts = config_dict['amountOfAccounts'] # try to make this number a multiple of 75 because Instaloader seems to rate-limit in periods of 75 requests
amount_of_posts_per_account = config_dict['amountOfPostsPerAccount']
email_to = config_dict['emailToAddress'] # "gabriel@gabrielromualdo.com"
email_from = config_dict['emailBotAddress'] # "bot@gabrielromualdo.com"
check_every = config_dict['cronjobPeriodMinutes'] # 240 in minutes

instagram_username = config_dict['igUsername']
instagram_password = config_dict['igPassword']
email_password = config_dict['emailBotPassword']
backend_auth_token = config_dict['backendAuthToken']
backend_baseurl = config_dict['backendBaseURL']

def send_email(subject, contents):
	subject = unidecode(str(subject).strip())
	contents = unidecode(str(contents).strip())

	# Details
	email = "bot@gabrielromualdo.com"
	password = email_password

	# SSL Details
	port = 587
	servername = "smtp.dreamhost.com"

	# Create a secure SSL context
	context = ssl.create_default_context()

	# Try to log in to server and send email
	server = smtplib.SMTP(servername, port)
	server.ehlo() # Can be omitted
	server.starttls(context=context) # Secure the connection
	server.ehlo() # Can be omitted
	server.login(email, password)

	server.sendmail(email, email_to, "Subject: " + subject + "\n\n" + contents)
	
	# exit server
	server.quit()

	print("\n===\n")
	print("Successfully sent email to {}".format(email_to))
	print("\nSubject: {}".format(subject))
	print("Contents:\n{}".format(contents))

def cronjob():
	accounts = []
	usernames = []

	# loop through pages of Tackalytics site which lists the most followed profiles
	# pages start at 1 and each page at the moment (2021-04-30) has 25 profiles
	for i in range(1, 1 + math.ceil(amount_of_accounts / 25)):
		req = None
		try:
			req = requests.get("https://www.trackalytics.com/the-most-followed-instagram-profiles/page/{}/".format(i))
		except Exception as e:
			# MOLF stands for More Or Less Followers. There is a resemblance to another abbreviation but that was not originally intended.
			send_email("MOLF: An Error Occurred Requesting Site", "Check the web server for more information. And that's all you need to know.")
			print("Error {}".format(e))
			return
		if(req.status_code == 200):
			try:
				html = req.text
				soup = BeautifulSoup(html, features="html.parser")
				for user_link in soup.select('table td a[title]'):
					username = user_link['href'].split("/")[-2]
					usernames.append(username)
			except Exception as e:
				print("Error: {}".format(e))
				send_email("MOLF: An Error Occurred", "An error occurred with the message: {}".format(e))
				break
		else:
			send_email("MOLF: An Error Occurred Requesting Site (HTTP {})".format(req.status_code), "And that's all you need to know.")
			print("Error {}".format(req.status_code))
			break
		print("Finished Scraping List Page {}".format(i))

	# instaloader is used to get data from Instagram
	instaloader_client = instaloader.Instaloader()
	instaloader_client.login(instagram_username, instagram_password)
	for i, username in enumerate(usernames):
		try:
			# create new account object and populate
			profile = instaloader.Profile.from_username(instaloader_client.context, username)
			account = {
				"followers": profile.followers,
				"name": profile.full_name,
				"username": username,
				"bio": profile.biography,
				"pictureURL": profile.profile_pic_url,
				"id": len(accounts) + 1, # yes, this means that IDs will be in order
				"postImageURLs": []
			}

			for post in profile.get_posts(): # loop through posts and note the first post's shortcode
				account["postImageURLs"].append(post.url)
				if len(account["postImageURLs"]) == amount_of_posts_per_account:
					break
			
			# error checking
			assert(account["followers"] > 0)
			assert(len(account["name"]) > 0)
			assert(len(account["pictureURL"]) > 0)
			assert(len(account["postImageURLs"]) == amount_of_posts_per_account)

			# add to final array
			accounts.append(account)
			print("Finished {}/{}: {}".format(i + 1, len(usernames), username))
		except Exception as e:
			pass

	# upload accounts data to server
	req = requests.post('{}/import-data.php'.format(backend_baseurl), headers={"x-auth-token": backend_auth_token}, json=accounts)
	if req.status_code == 200:
		print("Successfully uploaded data to backend.")
	else:
		send_email("MOLF: An Error Occurred", "An error occurred uploading data to server (HTTP {})".format(req.status_code))

# create the cronjob
schedule.every(check_every).minutes.do(cronjob)

# run the cronjob
cronjob()
while True:
	schedule.run_pending()
	sleep(30) # check to run the cronjob every 30 seconds