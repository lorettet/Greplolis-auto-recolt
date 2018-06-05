#!/usr/bin/python3

import requests
import json
import connect
import sys
from time import sleep
import threading 
import datetime

from queue import Queue

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
	def __init__(self, name, id, position):
		Town.__init__(self, name, id, position)
		
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
		s += " ".join(str(e) for e in self.towns)
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
	

	connect.connect(argv[1],argv[2])
	
	getInfo()
	

	print("Appuyez sur ENTRER pour arrêter le script")
	threadRecolt = AutoRecolt()
	threadRecolt.start()
	
	r = input()
	threadRecolt.event.set()
	
	
def getInfo():
	global islands
	
	"""Getting all player towns"""
	data='{"collections":{"Towns":[]},"town_id":'+connect.tid+',"nl_init":false}'
	r = connect.req.get("https://fr107.grepolis.com/game/frontend_bridge?town_id="+connect.tid+"&action=refetch&h="+connect.h+"&json="+data,headers={"X-Requested-With":"XMLHttpRequest"})
	j = r.json()
	towns = []
	for town in j["json"]["collections"]["Towns"]["data"]:
		towns += [PlayerTown(town["d"]["name"],town["d"]["id"], (town["d"]["island_x"],town["d"]["island_y"]))]

	"""Getting all farm towns"""
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
		print(island.q.qsize())
	
	
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
					self.getRessources(island.getNext(), farm)
			currTime = datetime.datetime.now()
			nextTime = currTime + datetime.timedelta(0,5*60)
			print("Prochaine récolte à "+nextTime.strftime("%H:%M"))
			self.event.wait(5*60)
			
				
	def getRessources(self, town, farm):
		url = "https://fr107.grepolis.com/game/frontend_bridge?action=execute&h="+connect.h
		global islands
		
		data = '{"model_url":"FarmTownPlayerRelation/'+str(farm.relation)+'","action_name":"claim","arguments":{"farm_town_id":"'+str(farm.id)+'","type":"resources","option":1},"town_id":"'+str(town.id)+'","nl_init":true}'
		r = connect.req.post(url, data={"json":data}, headers={"X-Requested-With":"XMLHttpRequest"})
		resp = r.json()
		if("success" in resp["json"]):
			print("Ressources livrees vers "+ town.name)
		else:
			print("Erreur : "+resp["json"]["error"])
			
	

if __name__ == "__main__":
	main(sys.argv)
			

