
from queue import Queue

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
			super().__setattr__('full', value != 0 and value*3 == self.iron + self.wood + self.stone)
		elif(name == 'iron'):
			super().__setattr__('full', self.storage != 0 and self.storage*3 == value + self.wood + self.stone)
		elif(name == 'wood'):
			super().__setattr__('full', self.storage != 0 and self.storage*3 == self.iron + value + self.stone)
		elif(name == 'stone'):
			super().__setattr__('full', self.storage != 0 and self.storage*3 == self.iron + self.wood + value)
			
		
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
