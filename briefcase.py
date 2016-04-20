class Briefcase:
	def __init__(self, number, amount):
		self.number = number
		self.amount = amount
		self.claimed = False
		self.open = False

	def getNumber(self):
		return self.number

	def getAmount(self):
		return self.amount

	def claimCase(self):
		self.claimed = True

	def openCase(self):
		self.open = True

	def isClaimed(self):
		return self.claimed

	def isOpen(self):
		return self.open