#!/usr/bin/python3 -u

import requests
import json
import connect
import sys
from time import sleep
import threading 
import datetime
from termcolor import colored
from queue import Queue
import signal

islands = []

"""Class Town"""
class Town:
	def __init__(self, name, id, position):
		self.name = name
		self.id = id
		self.position = position
		
	def __str__(self):
		return self.name
		
		
"""Class FarmTown"""	
class FarmTown(Town):
	def __init__(self, name, id, position, relation):
		Town.__init__(self, name, id, position)
		self.relation = relation

"""Class PlayerTown"""
class PlayerTown(Town):
	storage = 0
	wood = 0
	iron = 0
	stone = 0
	full = False
	units = {}
	def __init__(self, name, id, position):
		Town.__init__(self, name, id, position)
		
	def __str__(self):
		return self.name+": storage "+str(self.storage)+" iron "+str(self.iron)+" wood "+str(self.wood)+" stone "+str(self.stone)
	
	def __setattr__(self,name,value):
		super().__setattr__(name, value)
		if(name == 'storage'):
			super().__setattr__('full', value != 0 and value == self.iron + self.wood + self.stone)
		elif(name == 'iron'):
			super().__setattr__('full', self.storage != 0 and self.storage == value + self.wood + self.stone)
		elif(name == 'wood'):
			super().__setattr__('full', self.storage != 0 and self.storage == self.iron + value + self.stone)
		elif(name == 'stone'):
			super().__setattr__('full', self.storage != 0 and self.storage == self.iron + self.wood + value)
			
		
"""Class Island"""
class Island:
	def __init__(self, position):
		self.position = position
		self.farms = []
		self.q = Queue()
		self.__dict__["towns"]=[]
		
	def addPlayerTown(self, town):
		self.towns += town
		
	def addFarmTown(self, farm):
		self.farms += town
		
	def __str__(self):
		s =  "("+str(self.position[0])+","+str(self.position[1])+") : \n\t"
		s += " ".join(e.name for e in self.towns)
		s += "\n\t"
		s += " ".join(str(e) for e in self.farms)
		return s

	def getNext(self):
		t = self.q.get_nowait()
		self.q.put_nowait(t)
		return t
		
	def __setattr__(self, name, value):
		if name == "towns":
			self.q.put_nowait(value[len(value)-1])
		super().__setattr__(name, value)



def usage():
	print("Usage : "+sys.argv[0] + " login password")

def main(argv):
	
	if(len(argv) != 3):
		usage()
		exit()
	
	global login, passwd
	login = argv[1]
	passwd = argv[2]
	connect.connect(login,passwd)
	
	getInfo()
	
	global threadRecolt
	threadRecolt.start()
	signal.signal(signal.SIGINT, close_thread)
	
	threadRecolt.join()
	
	print("Bye!")
	
"""Get all usefull info"""
def getInfo():
	global islands
	
	"""Getting all player towns"""
	towns = getTownsInfo()

	"""Getting all farm towns"""
	farms = getFarmsInfo()
		
	"""Creating islands"""
	for town in towns:
		trouvee = False
		for island in islands:
			if(island.position == town.position):
				island.towns += [town]
				trouvee = True
				break
		if not trouvee:
			island = Island(town.position)
			islands += [island]
			island.towns += [town]
			
	for farm in farms:
		for island in islands:
			if(island.position == farm.position):
				island.farms += [farm]
				trouvee = True
				break
				
	for island in islands:
		print(island)
		
"""Get usefull infos of all towns"""
def getTownsInfo():
	data='{"collections":{"Towns":[]},"town_id":'+connect.tid+',"nl_init":false}'
	r = connect.req.get("https://fr107.grepolis.com/game/frontend_bridge?town_id="+connect.tid+"&action=refetch&h="+connect.h+"&json="+data,headers={"X-Requested-With":"XMLHttpRequest"})
	j = r.json()
	towns = []
	for town in j["json"]["collections"]["Towns"]["data"]:
		theTown = PlayerTown(town["d"]["name"],town["d"]["id"], (town["d"]["island_x"],town["d"]["island_y"]))
		theTown.storage = town["d"]["storage"]
		theTown.iron = town["d"]["resources"]["iron"]
		theTown.wood = town["d"]["resources"]["wood"]
		theTown.stone = town["d"]["resources"]["stone"]
		towns += [theTown]
	return towns
	
"""Update town info"""
def updateTownInfo():
	global islands
	towns = getTownsInfo()
	for island in islands:
		for i in range(len(island.towns)):
			for infoTown in towns:
				if island.towns[i].id == infoTown.id:
					island.towns[i].storage = infoTown.storage
					island.towns[i].wood = infoTown.wood
					island.towns[i].iron = infoTown.iron
					island.towns[i].stone = infoTown.stone
					

"""Get usefull infos of all farms"""
def getFarmsInfo():
	data = '{"types":[{"type":"easterIngredients"},{"type":"map","param":{"x":15,"y":7}},{"type":"bar"},{"type":"backbone"}],"town_id":'+connect.tid+',"nl_init":false}'
	r = connect.req.post("https://fr107.grepolis.com/game/data?town_id="+connect.tid+"&action=get&h="+connect.h, data={"json":data}, headers={"X-Requested-With":"XMLHttpRequest"})
	j = r.json()
	farms = []
	for farm in j["json"]["backbone"]["collections"][25]["data"]:
		farm_id = farm["d"]["id"]
		relations = j["json"]["backbone"]["collections"][26]["data"]
		index = 0
		while(relations[index]["d"]["farm_town_id"] != farm_id):
			index += 1
			
		farms += [FarmTown(farm["d"]["name"], farm_id, (farm["d"]["island_x"],farm["d"]["island_y"]), relations[index]["d"]["id"])]
	return farms
		
"""Thread that allow autorecolt"""
class AutoRecolt(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		
	def run(self):
		index_town = 0
		global islands
		
		while not self.event.is_set():
			print("Début de la récolte...")
			for island in islands:
				for farm in island.farms:
					nextTown = island.getNext()
					if not nextTown.full:
						ok = self.getRessources(nextTown, farm)
						intent = 1
						while(not ok and intent != 4):
							print("Nouvelle connexion dans 30min")
							self.event.wait(30*60)
							print("Reconnexion...")
							connect.connect_game()
							print("Nouvelle tentative...")
							ok = self.getRessources(nextTown, farm)
							intent += 1
						
						if(intent == 4):
							print(colored("[ERROR] Fermeture de la session de récolte",'red'))
							return
					else:
						print(colored('[WARNING] '+nextTown.name+' est pleine!','yellow'))
			updateTownInfo()
			currTime = datetime.datetime.now()
			nextTime = currTime + datetime.timedelta(0,5*60)
			print("Prochaine récolte à "+nextTime.strftime("%H:%M"))
			self.event.wait(5*60)
			
		print("Fermeture de la session de récolte")
			
				
	def getRessources(self, town, farm):
		url = "https://fr107.grepolis.com/game/frontend_bridge?action=execute&h="+connect.h
		global islands
		
		data = '{"model_url":"FarmTownPlayerRelation/'+str(farm.relation)+'","action_name":"claim","arguments":{"farm_town_id":"'+str(farm.id)+'","type":"resources","option":1},"town_id":"'+str(town.id)+'","nl_init":true}'

		r = connect.req.post(url, data={"json":data}, headers={"X-Requested-With":"XMLHttpRequest"})
		resp = r.json()
		if("success" in resp["json"]):
			print("Ressources livrées vers "+ town.name)
			return True
		else:
			if('redirect' in resp["json"]):
				print(colored("[ERROR] Erreur lors de la livraison des ressources : joueur déconnecté",'red'))
				return False
			print(colored("[WARNING] Erreur lors de la livraison des ressources : "+resp["json"]["error"],'yellow'))
			return True
			
"""Close thread properly"""
def close_thread(sig, frame):
	global threadRecolt
	print("Closing thread autorecolt")
	threadRecolt.event.set()

threadRecolt = AutoRecolt()

if __name__ == "__main__":
	main(sys.argv)
			

