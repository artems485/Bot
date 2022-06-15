from datetime import datetime, timedelta
import requests

def list_of_checks(user_mail, user_token):
	start_date = f'after:{(datetime.today()-timedelta(days=92)).strftime("%Y/%m/%d")}'
	check_sendler = 'from:noreply@taxcom.ru'
	search_params = f'{start_date} {check_sendler}'
	parameters = dict(access_token = user_token)
	resp = requests.get(f'https://gmail.googleapis.com/gmail/v1/users/{user_mail}/messages?access_token={user_token}')
	return resp.text()

def checks_parser():
	pass
