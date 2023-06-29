import telebot
from telebot import types
import webbrowser
import sqlite3
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
import hashlib
from argon2 import PasswordHasher
import random
from datetime import datetime

bot = telebot.TeleBot('XXXXX')
user_name = None 
user_key_password = None 
first_adress = None
second_adress = None
count = None
id_user_who_want_taxi = None
driver_name = None
driver_password = None
driver_car_type = None
driver_car_number = None
driver_face_photo = None



@bot.message_handler(commands = ['start'])
def start_mess(message):
	bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}, я бот для заказа такси.\nПодробнее с моим функционалом ты можешь ознакомиться введя команду /help')
	


@bot.message_handler(commands = ['help'])
def help_mess(message):
	text_to_help_user = '''Ниже приведены все команды бота
	<b>
	/start - Начать диалог
	/help - Меню команд
	/order_taxi - Заказать такси
	/register_as_user - Зарегестрироваться как пользователь
	/register_as_driver - Зарегестрироваться как таксист
	/start_work - Выйти на линию (Для таксистов)
	/stop_work - Уйти с линии (Для таксистов)
	/money - Внутренний кошелек
	</b>'''
	bot.send_message(message.chat.id, text_to_help_user, parse_mode = 'html')

@bot.message_handler(commands = ['order_taxi'])
def order_new_taxi(message):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT id FROM users WHERE tg_id = '%s'" % (message.chat.id))
	list_of_this_user = cur.fetchall()
	cur.close()
	if len(list_of_this_user) >= 1:
		bot.send_message(message.chat.id, 'Введите адрес, где вы сейчас находитесь\nФормат адреса: ул.Ленина, 1, Москва')
		bot.register_next_step_handler(message, get_first_adress)
	else:
		messege_to_unregistered_user = '''Вы еще не зарегестровались в системе
		Сделайте это введя команду /register_as_user'''
		bot.send_message(message.chat.id, messege_to_unregistered_user)
	database.close()

def get_first_adress(message):
	global first_adress
	first_adress = message.text
	bot.send_message(message.chat.id, 'Введите адресс, куда нужно доехать\nФормат адреса: ул.Ленина, 1, Москва')
	bot.register_next_step_handler(message, get_second_adress)

def get_second_adress(message):
	global count
	global first_adress
	global second_adress
	second_adress = message.text
	geolocator = Nominatim(user_agent = 'bot')
	try:
		location1 = geolocator.geocode(first_adress)
		location2 = geolocator.geocode(second_adress)
		gps_point1 = location1.latitude, location2.longitude
		gps_point2 = location2.latitude, location2.longitude
		count = int((geodesic(gps_point1, gps_point2).kilometers * 20) + 70)
		if count >= 120:
			count = count
		else:
			count = 120
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (message.chat.id))
		list_balance = cur.fetchall()
		balance = None
		for el in list_balance:
			balance = el[4]
		cur.close()
		database.close()
		markup = types.InlineKeyboardMarkup()
		btn1 = types.InlineKeyboardButton('Да', callback_data = 'agree_to_drive_as_user')
		btn2 = types.InlineKeyboardButton('Нет', callback_data = 'disagree_to_drive_as_user')
		markup.row(btn1, btn2)
		bot.send_message(message.chat.id, f'Цена поездки: {str(count)} рублей.\nВаш баланс: {str(balance)}.\nВы согласны на поездку?', reply_markup = markup)
	except:
		bot.send_message(message.chat.id, 'Похоже, что адреса были введены неверно')

	

@bot.message_handler(commands = ['register_as_user'])
def i_am_new_user(message):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT id FROM users WHERE tg_id = '%s'" % (message.chat.id))
	list_of_this_user = cur.fetchall()
	cur.close()
	if len(list_of_this_user) == 0:
		bot.send_message(message.chat.id, 'Введите свое имя')
		bot.register_next_step_handler(message, get_user_name)
	else:
		bot.send_message(message.chat.id, 'Вы уже зарегестрированны как пользователь')
	database.close()

def get_user_name(message):
	global user_name
	user_name = message.text.strip()
	bot.send_message(message.chat.id, 'Введите пароль')
	bot.register_next_step_handler(message, get_user_password)

def get_user_password(message):
	global user_key_password
	passs = message.text.strip()
	ph = PasswordHasher()
	user_key_password = ph.hash(passs)
	bot.send_message(message.chat.id, 'Скинь мне фотографию своего лица')
	bot.register_next_step_handler(message, get_user_face_photo)

def get_user_face_photo(message):
	if message.content_type == 'photo':
		file_photo = bot.get_file(message.photo[-1].file_id)
		downloaded_file_photo = bot.download_file(file_photo.file_path)
		src = 'photos/' + message.photo[1].file_id + '.jpg'
		with open(src, 'wb') as new_file:
			new_file.write(downloaded_file_photo)
		global user_name
		global user_key_password
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("INSERT INTO users (tg_id, name, password, money, face_photo) VALUES ('%s', '%s', '%s', '%s', '%s')" % (message.chat.id, user_name, user_key_password, 0, src))
		database.commit()
		cur.close()
		database.close()
		bot.send_message(message.chat.id, 'Вы успешно зарегестрировались как пользователь')
		user_name = None
		user_key_password = None
	else:
		bot.send_message(message.chat.id, 'Это не фото, попробуй еще раз')
		bot.register_next_step_handler(message, get_user_face_photo)


@bot.message_handler(commands = ['register_as_driver'])
def i_am_new_driver(message):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
	list_of_this_drivers = cur.fetchall()
	cur.close()
	if len(list_of_this_drivers) == 0:
		bot.send_message(message.chat.id, 'Введите свое имя')
		bot.register_next_step_handler(message, get_driver_name)
	else:
		bot.send_message(message.chat.id, 'Вы уже зарегестрированны как водитель')
	database.close()

def get_driver_name(message):
	global driver_name
	driver_name = message.text.strip()
	bot.send_message(message.chat.id, 'Введите пароль')
	bot.register_next_step_handler(message, get_driver_password)

def get_driver_password(message):
	global driver_password
	passs = message.text.strip()
	ph = PasswordHasher()
	driver_password = ph.hash(passs)
	bot.send_message(message.chat.id, 'Введите название вашего автомобиля')
	bot.register_next_step_handler(message, get_car_model)

def get_car_model(message):
	global driver_car_type
	driver_car_type = message.text.strip()
	bot.send_message(message.chat.id, 'Введите номер вашего автомобиля')
	bot.register_next_step_handler(message, get_driver_num)

def get_driver_num(message):
	global driver_car_number
	driver_car_number = message.text.strip()
	bot.send_message(message.chat.id, 'Скинь мне фото своего лица')
	bot.register_next_step_handler(message, get_driver_face_photo)

def get_driver_face_photo(message):
	global driver_face_photo
	if message.content_type == 'photo':
		file_photo = bot.get_file(message.photo[-1].file_id)
		downloaded_file_photo = bot.download_file(file_photo.file_path)
		src = 'photos/' + message.photo[1].file_id + '.jpg'
		with open(src, 'wb') as new_file:
			new_file.write(downloaded_file_photo)
		driver_face_photo = src
		bot.send_message(message.chat.id, 'Скинь мне фото своей машины')
		bot.register_next_step_handler(message, get_driver_car_photo)
	else:
		bot.send_message(message.chat.id, 'Это не фото, попробуй еще раз')
		bot.register_next_step_handler(message, get_driver_face_photo)

def get_driver_car_photo(message):
	if message.content_type == 'photo':
		file_photo = bot.get_file(message.photo[-1].file_id)
		downloaded_file_photo = bot.download_file(file_photo.file_path)
		src = 'photos/' + message.photo[1].file_id + '.jpg'
		with open(src, 'wb') as new_file:
			new_file.write(downloaded_file_photo)
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("INSERT INTO drivers (tg_id, name, password, money, activity, car_type, car_number, face_photo, car_photo) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (message.chat.id, driver_name, driver_password, 0, 0, driver_car_type, driver_car_number, driver_face_photo, src))
		database.commit()
		cur.close()
		database.close()
		bot.send_message(message.chat.id, 'Вы успешно зарегестрировались как водитель')
	else:
		bot.send_message(message.chat.id, 'Это не фото, попробуй еще раз')
		bot.register_next_step_handler(message, get_driver_car_photo)


@bot.message_handler(commands = ['start_work'])
def go_in_line(message):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
	list_active_notactive_drivers = cur.fetchall()
	if len(list_active_notactive_drivers) > 0:
		this_driver = None
		for el in list_active_notactive_drivers:
			this_driver = el
		if el[5] == 0:
			cur.execute("UPDATE drivers SET activity = 1 WHERE tg_id = '%s'" % (message.chat.id))
			database.commit()
			bot.send_message(message.chat.id, 'Вы вышли на линию, ожидайте заказов')
		else:
			bot.send_message(message.chat.id, 'Вы уже находитесь на линии')
	else:
		bot.send_message(message.chat.id, 'Вы не зарегестрированны как водитель\nСделйте это написав команду /register_as_driver')
	cur.close()
	database.close()


@bot.message_handler(commands = ['stop_work'])
def go_out_line(message):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
	list_active_notactive_drivers = cur.fetchall()
	if len(list_active_notactive_drivers) > 0:
		this_driver = None
		for el in list_active_notactive_drivers:
			this_driver = el
		if el[5] == 1:
			cur.execute("UPDATE drivers SET activity = 0 WHERE tg_id = '%s'" % (message.chat.id))
			database.commit()
			bot.send_message(message.chat.id, 'Вы ушли с линии, можете отдохнуть')
		else:
			bot.send_message(message.chat.id, 'Вы еще не были на линии')
	else:
		bot.send_message(message.chat.id, 'Вы не зарегестрированны как водитель\nСделйте это написав команду /register_as_driver')
	cur.close()
	database.close()

@bot.message_handler(commands = ['money'])
def my_money(message):
	markup = types.InlineKeyboardMarkup()
	btn1 = types.InlineKeyboardButton('Пользователь', callback_data = 'i_am_a_user')
	btn2 = types.InlineKeyboardButton('Водитель', callback_data = 'i_am_a_driver')
	markup.row(btn1, btn2)
	bot.send_message(message.chat.id, 'В качестве кого вы хотите зайти в кошелек?', reply_markup = markup)


@bot.callback_query_handler(func = lambda callback: True)	
def callback_message(callback):
	global id_user_who_want_taxi
	global first_adress
	global second_adress
	if callback.data == 'agree_to_drive_as_user':
		balance = find_my_balance(callback.message.chat.id)
		global count
		if balance >= count:
			bot.edit_message_text('Ожидайте такси', callback.message.chat.id, callback.message.message_id)
			id_user_who_want_taxi = callback.message.chat.id
			find_active_cars()
		else:
			bot.edit_message_text('Вам не хватает денег на счету', callback.message.chat.id, callback.message.message_id)
			count = None
	elif callback.data == 'disagree_to_drive_as_user':
		bot.edit_message_text('Вы отменили поездку', callback.message.chat.id, callback.message.message_id)
	elif callback.data == 'agree_to_drive_as_driver':
		bot.edit_message_text(f'Активный заказ\nПервый адрес: {first_adress}\nВторой адрес: {second_adress}\nДля завершения поездки введите команду /end_drive', callback.message.chat.id, callback.message.message_id)
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (callback.message.chat.id))
		list_drivers = cur.fetchall()
		dri_name = None
		dri_car = None
		dri_car_name = None
		dri_car_num = None
		for el in list_drivers:
			dri_name = el[2]
			dri_car = el[9]
			dri_car_name = el[6]
			dri_car_num = el[7]
		cur.execute("UPDATE drivers SET activity = 0 WHERE tg_id = '%s'" % (callback.message.chat.id))
		database.commit()
		cur.close()
		database.close()
		bot.send_message(id_user_who_want_taxi, f'К вам подьедет {dri_name} на {dri_car_name} с номером {dri_car_num}')
		file_photo_car = open('./' + dri_car, 'rb')
		bot.send_photo(id_user_who_want_taxi, file_photo_car)
		bot.register_next_step_handler(callback.message, driving_end)
	elif callback.data == 'disagree_to_drive_as_driver':
		bot.edit_message_text('Вы отменили заказ', callback.message.chat.id, callback.message.message_id)
		find_active_cars()
	elif callback.data == 'i_am_a_user':
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (callback.message.chat.id))
		list_this_user = cur.fetchall()
		if len(list_this_user) > 0:
			bot.edit_message_text('Введите пароль', callback.message.chat.id, callback.message.message_id)
			bot.register_next_step_handler(callback.message, checking_user_password)
		else:
			bot.edit_message_text('Вы еще не зарегестрированны как пользователь\nСделйте это введя команду /register_as_user', callback.message.chat.id, callback.message.message_id)
		cur.close()
		database.close()
	elif callback.data == 'i_am_a_driver':
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (callback.message.chat.id))
		list_this_driver = cur.fetchall()
		if len(list_this_driver) > 0:
			bot.edit_message_text('Введите пароль', callback.message.chat.id, callback.message.message_id)
			bot.register_next_step_handler(callback.message, checking_driver_password)
		else:
			bot.edit_message_text('Вы еще не зарегестрированны как пользователь\nСделйте это введя команду /register_as_user', callback.message.chat.id, callback.message.message_id)
		cur.close()
		database.close()
	elif callback.data == 'add_money_user':
		bot.edit_message_text('Введите количество денег для пополнения, в рублях, без копеек', callback.message.chat.id, callback.message.message_id)
		bot.register_next_step_handler(callback.message, how_much_add_user)
	elif callback.data == 'remove_money_user':
		bot.edit_message_text('Введите количество денег для вывода, в рублях, без копеек', callback.message.chat.id, callback.message.message_id)
		bot.register_next_step_handler(callback.message, how_much_remove_user)
	elif callback.data == 'go_back_money_user':
		bot.edit_message_text('Вы вышли из кошелька', callback.message.chat.id, callback.message.message_id)
	elif callback.data == 'remove_money_driver':
		bot.edit_message_text('Введите количество денег для вывода, в рублях, без копеек', callback.message.chat.id, callback.message.message_id)
		bot.register_next_step_handler(callback.message, how_much_remove_driver)
	elif callback.data == 'go_back_money_driver':
		bot.edit_message_text('Вы вышли из кошелька', callback.message.chat.id, callback.message.message_id)

def checking_driver_password(message):
	passs = message.text.strip()
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
	list_this_driver = cur.fetchall()
	this_driver = None
	this_driver_balance = None
	for el in list_this_driver:
		this_driver = el[3]
		this_driver_balance = el[4]
	ph = PasswordHasher()
	if ph.verify(this_driver, passs):
		markup = types.InlineKeyboardMarkup()
		btn1 = types.InlineKeyboardButton('Вывести', callback_data = 'remove_money_driver')
		btn2 = types.InlineKeyboardButton('Выйти', callback_data = 'go_back_money_driver')
		markup.row(btn1, btn2)
		bot.send_message(message.chat.id, f'Ваш баланс: {this_driver_balance} рублей', reply_markup = markup)
	else:
		bot.send_message(message.chat.id, 'Пароль введен неверно')
	cur.close()
	database.close()

def how_much_remove_driver(message):
	money_by_text = message.text.strip()
	if money_by_text.isdigit():
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
		list_this_balance = cur.fetchall()
		this_balance = None
		for el in list_this_balance:
			this_balance = el[4]
		if int(money_by_text) <= this_balance:
			money_to_remove = this_balance - int(money_by_text)
			cur.execute("UPDATE drivers SET money = '%s' WHERE tg_id = '%s'" % (int(money_to_remove), message.chat.id))
			database.commit()
			bot.send_message(message.chat.id, 'Вы вывели деньги с кошелька')
		else:
			bot.send_message(message.chat.id, 'Вы ввели число превышающее ваш баланс, попробуйте еще раз')
			bot.register_next_step_handler(message, how_much_remove_driver)
		cur.close()
		database.close()
	else:
		bot.send_message(message.chat.id, 'Кажется вы неправильно ввели число, попробуйте еще раз')
		bot.register_next_step_handler(message, how_much_remove_driver)


def checking_user_password(message):
	passs = message.text.strip()
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (message.chat.id))
	list_this_user = cur.fetchall()
	this_user = None
	this_user_balance = None
	for el in list_this_user:
		this_user = el[3]
		this_user_balance = el[4]
	ph = PasswordHasher()
	if ph.verify(this_user, passs):
		markup = types.InlineKeyboardMarkup()
		btn1 = types.InlineKeyboardButton('Пополнить', callback_data = 'add_money_user')
		btn2 = types.InlineKeyboardButton('Вывести', callback_data = 'remove_money_user')
		btn3 = types.InlineKeyboardButton('Выйти', callback_data = 'go_back_money_user')
		markup.row(btn1, btn2)
		markup.row(btn3)
		bot.send_message(message.chat.id, f'Ваш баланс: {this_user_balance} рублей', reply_markup = markup)
	else:
		bot.send_message(message.chat.id, 'Пароль введен неверно')
	cur.close()
	database.close()

def how_much_add_user(message):
	money_by_text = message.text.strip()
	if money_by_text.isdigit():
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (message.chat.id))
		list_f_b = cur.fetchall()
		f_b = None
		for el in list_f_b:
			f_b = el[4]
		money_to_add = f_b + int(money_by_text)
		cur.execute("UPDATE users SET money = '%s' WHERE tg_id = '%s'" % (int(money_to_add), message.chat.id))
		database.commit()
		bot.send_message(message.chat.id, 'Вы пополнили кошелек')
		cur.close()
		database.close()
	else:
		bot.send_message(message.chat.id, 'Кажется вы неправильно ввели число, попробуйте еще раз')
		bot.register_next_step_handler(message, how_much_add_user)

def how_much_remove_user(message):
	money_by_text = message.text.strip()
	if money_by_text.isdigit():
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (message.chat.id))
		list_this_balance = cur.fetchall()
		this_balance = None
		for el in list_this_balance:
			this_balance = el[4]
		if int(money_by_text) <= this_balance:
			money_to_remove = this_balance - int(money_by_text)
			cur.execute("UPDATE users SET money = '%s' WHERE tg_id = '%s'" % (int(money_to_remove), message.chat.id))
			database.commit()
			bot.send_message(message.chat.id, 'Вы вывели деньги с кошелька')
		else:
			bot.send_message(message.chat.id, 'Вы ввели число превышающее ваш баланс, попробуйте еще раз')
			bot.register_next_step_handler(message, how_much_remove_user)
		cur.close()
		database.close()
	else:
		bot.send_message(message.chat.id, 'Кажется вы неправильно ввели число, попробуйте еще раз')
		bot.register_next_step_handler(message, how_much_remove_user)

def find_my_balance(idishnik):
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (idishnik))
	list_this_user = cur.fetchall()
	balance = None
	for el in list_this_user:
		balance = el[4]
	cur.close()
	database.close()
	return balance

def find_active_cars():
	global first_adress
	global second_adress
	global id_user_who_want_taxi
	global count
	database = sqlite3.connect('taxi.db')
	cur = database.cursor()
	cur.execute("SELECT * FROM drivers WHERE activity = 1")
	list_active_drivers = cur.fetchall()
	new_list_active_drivers = list()
	for el in list_active_drivers:
		new_list_active_drivers.append(el[1])
	if len(new_list_active_drivers) >= 1:
		random_index = random.randint(0, len(new_list_active_drivers) - 1)
		mess_to_driver = f'''У вас новый заказ, цена поездки: {int(count * 0.9)}
		Точка А: {first_adress}
		Точка Б: {second_adress}'''
		markup = types.InlineKeyboardMarkup()
		markup.add(types.InlineKeyboardButton('Согласиться', callback_data = 'agree_to_drive_as_driver'))
		markup.add(types.InlineKeyboardButton('Отменить', callback_data = 'disagree_to_drive_as_driver'))
		bot.send_message(new_list_active_drivers[random_index], mess_to_driver, reply_markup = markup)
	else:
		bot.send_message(id_user_who_want_taxi, 'На данный момент у нас нет свободных водителей, попробуйте позже')
	cur.close()
	database.close()

def driving_end(message):
	global id_user_who_want_taxi
	global first_adress
	global second_adress
	global count
	text_by_driver = message.text
	if text_by_driver == '/end_drive':
		bot.send_message(message.chat.id, 'Поездка завершена! Спасибо что работаете на наше такси!')
		bot.send_message(id_user_who_want_taxi, 'Поездка завершена! Спасибо что пользуетесь нашим такси!')
		database = sqlite3.connect('taxi.db')
		cur = database.cursor()
		cur.execute("UPDATE drivers SET activity = 1 WHERE tg_id = '%s'" % (message.chat.id))
		database.commit()
		cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
		list_bal1 = cur.fetchall()
		bal1 = 0
		for el in list_bal1:
			bal1 = el[4]
		cur.execute("UPDATE drivers SET money = '%s' WHERE tg_id = '%s'" % (bal1 + int(count * 0.9), message.chat.id))
		database.commit()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (id_user_who_want_taxi))
		list_bal2 = cur.fetchall()
		bal2 = 0
		for element in list_bal2:
			bal2 = element[4]
		cur.execute("UPDATE users SET money = '%s' WHERE tg_id = '%s'" % (bal2 - count, id_user_who_want_taxi))
		database.commit()
		cur.execute("SELECT * FROM taxi_owner_money WHERE id = 1")
		list_bal3 = cur.fetchall()
		bal3 = 0
		for ell in list_bal3:
			bal3 = ell[1]
		cur.execute("UPDATE taxi_owner_money SET money = '%s' WHERE id = 1" % (bal3 + int(count * 0.1)))
		database.commit()
		cur.execute("SELECT * FROM users WHERE tg_id = '%s'" % (id_user_who_want_taxi))
		list_us = cur.fetchall()
		real_id_user = None
		for el in list_us:
			real_id_user = el[0]
		cur.execute("SELECT * FROM drivers WHERE tg_id = '%s'" % (message.chat.id))
		list_dr = cur.fetchall()
		real_id_driver = None
		for el1 in list_dr:
			real_id_driver = el1[0]
		starting_time = str(datetime.now())
		stopping_time = str(datetime.now())
		cur.execute("INSERT INTO history (id_user, id_driver, time_start, time_stop, first_adress, second_adress, cost, driver_earn) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s')" %(real_id_user, real_id_driver, starting_time, stopping_time, first_adress, second_adress, count, int(count * 0.9)))
		database.commit()
		cur.close()
		database.close()
		id_user_who_want_taxi = None
		first_adress = None
		second_adress = None
		count = None
	else:
		bot.register_next_step_handler(message, driving_end)



bot.polling(none_stop = True)