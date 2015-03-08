#Rutina prototipo para controlar y  leer el estado del puerto digital GPIO
#El proposito es controlar un circuito de 2 relays
#Para control se eligen los pines GPIO 25 y 17 identificados segun el nombre BCM (no segun la posicion en la placa)
#Para lectura se eligen los pines GPIO 23 y 24
# Para propositos de feedback el pin 23 debe conectarse al 25 y el 17 al 24.

import RPi.GPIO as GPIO

import time

relay1 = 25
relay2 = 17
relay1_read = 23
relay2_read = 24

def init():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(relay1_read, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
	GPIO.setup(relay2_read, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	GPIO.setup(relay1, GPIO.OUT)
	GPIO.setup(relay2, GPIO.OUT)
	GPIO.add_event_detect(relay1_read, GPIO.RISING, callback=printRelay1, bouncetime=300)
	GPIO.add_event_detect(relay2_read, GPIO.FALLING, callback=printRelay2, bouncetime=300)

def printRelay1(channel):
	print("Button 1 pressed!")

def printRelay2(channel):
	print("Button 2 pressed!")

def end():
	GPIO.cleanup()
	GPIO.remove_event_detect(relay1_read)
	GPIO.remove_event_detect(relay2_read)
def on(pin):
	GPIO.output(pin, True)

def off(pin):
	GPIO.output(pin, False)

def status():
	relay1 = GPIO.input(relay1_read)
	relay2 = GPIO.input(relay2_read)
	print "relay 1: " + str(relay1)
	print "relay 2: " + str(relay2)

def R1(state):
	if state:
		on(relay1)
	else:
		off(relay1)

def R2(state):
	if state:
		on(relay2)
	else:
		off(relay2)




