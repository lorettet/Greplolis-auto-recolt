#!/usr/bin/python3

import requests
import sys 
import json

req = requests.Session()
playerId=""
h=""
tid=""

def connect(login, pwd):
	global req, playerId,h,tid
	print("Tentative de connexion...")
	r = req.get("https://fr.grepolis.com")
	data={"login[userid]":login,"login[password]":pwd,"login[remember_me]":"false"}
	r = req.post("https://fr.grepolis.com/glps/login_check", data=data, headers={"X-Requested-With":"XMLHttpRequest","X-XSRF-TOKEN":req.cookies.get("XSRF-TOKEN")})
	j= r.json()
	playerId=""
	if(j["success"]):
		print("Identification correct")
		playerId=str(j["player_id"])
		print("Player id : "+playerId)
	else:
		print("Problème d'identification")
		print(j["errors"]["error"]["message"])
		return False

	print("Tentative de connexion à la liste des serveurs...")
	r=req.get("https://fr.grepolis.com")
	if(r.url == "https://fr.grepolis.com/"):
		print("Echec lors de la connexion à la liste des serveurs")
		return False
		
	print("Tentative de connexion au jeu...")
	r=req.post("https://fr0.grepolis.com/start?action=login_to_game_world",data={"world":"fr107","name":login})
	if(r.url == "https://fr.grepolis.com/"):
		print("Echec lors de la connexion au jeu")
		return False
	pos = r.text.find("csrfToken") +len("csrfToken") + 3
	h=r.text[pos:pos+40]
	pos = r.text.find("townId") + 2 + len("townId")
	tid=r.text[pos:pos+5]
	print("Connexion réussi!")
	return True

