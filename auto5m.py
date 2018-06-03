#!/usr/bin/python3

import requests
import json
import connect
import sys
from time import sleep
import threading 
import datetime

towns=[]
farms=[]
farmRelations={}
townsMap={}

def usage():
	print("Usage : "+sys.argv[0] + " login password")

def main(argv):
	
	if(len(argv) != 3):
		usage()
		exit()
	
	connect.connect(argv[1],argv[2])
	
	global towns, farms, farmRelations, townsMap
	data='{"collections":{"Towns":[]},"town_id":'+connect.tid+',"nl_init":false}'
	r = connect.req.get("https://fr107.grepolis.com/game/frontend_bridge?town_id="+connect.tid+"&action=refetch&h="+connect.h+"&json="+data,headers={"X-Requested-With":"XMLHttpRequest"})
	j = r.json()
	for town in j["json"]["collections"]["Towns"]["data"]:
		towns += [{"id":town["d"]["id"], "name":town["d"]["name"], "island":(town["d"]["island_x"],town["d"]["island_y"])}]
		townsMap[town["d"]["id"]] = town["d"]["name"]

	data = '{"types":[{"type":"easterIngredients"},{"type":"map","param":{"x":15,"y":7}},{"type":"bar"},{"type":"backbone"}],"town_id":'+connect.tid+',"nl_init":false}'
	r = connect.req.post("https://fr107.grepolis.com/game/data?town_id="+connect.tid+"&action=get&h="+connect.h, data={"json":data}, headers={"X-Requested-With":"XMLHttpRequest"})
	j = r.json()
	for farm in j["json"]["backbone"]["collections"][25]["data"]:
		farms += [{"id":farm["d"]["id"],"name":farm["d"]["name"], "island":(farm["d"]["island_x"],farm["d"]["island_y"])}]

	for relation in j["json"]["backbone"]["collections"][26]["data"]: 
		farmRelations[relation["d"]["farm_town_id"]] = relation["d"]["id"] 	

	print("Appuyez sur ENTRER pour arrêter le script")
	threadRecolt = AutoRecolt()
	threadRecolt.start()
	
	r = input()
	threadRecolt.event.set()
	
	
		
class AutoRecolt(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		
	def run(self):
		index_town = 0
		global farms, farmRelations, towns, townsMap
		
		while not self.event.is_set():
			print("Début de la récolte...")
			for farm in farms:
				relation = farmRelations[farm["id"]]
				while(towns[index_town]["island"] != farm["island"]):
					index_town+=1
					if(index_town >= len(towns)):
						index_town=0
				self.getRessources(towns[index_town]["id"],farm["id"],relation)
				index_town+=1
				if(index_town >= len(towns)):
					index_town=0
			currTime = datetime.datetime.now()
			nextTime = currTime + datetime.timedelta(0,5*60)
			print("Prochaine récolte à "+nextTime.strftime("%H:%M"))
			self.event.wait(5*60)
			
				
	def getRessources(self, tid, fid, r):
		url = "https://fr107.grepolis.com/game/frontend_bridge?action=execute&h="+connect.h
		global towns, farms, farmRelations, townsMap
		
		data = '{"model_url":"FarmTownPlayerRelation/'+str(r)+'","action_name":"claim","arguments":{"farm_town_id":"'+str(fid)+'","type":"resources","option":1},"town_id":"'+str(tid)+'","nl_init":true}'
		r = connect.req.post(url, data={"json":data}, headers={"X-Requested-With":"XMLHttpRequest"})
		resp = r.json()
		if("success" in resp["json"]):
			print("Ressources livrees vers "+ townsMap[tid])
		else:
			print("Erreur : "+resp["json"]["error"])
			
	
		
if __name__ == "__main__":
	main(sys.argv)
			
