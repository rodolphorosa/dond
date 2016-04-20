class Contestant:

	def __init__(self):
		self.mybriefcase = None
		self.gain = None

	def claimBriefcase(self, briefcase):
		if not self.mybriefcase:
			self.mybriefcase = briefcase
			return True
		else: 
			return False

	def getBriefcase(self):
		return self.mybriefcase

	def acceptOffer(self, offer):
		self.gain = offer

	def getPrize(self):
		self.gain = self.mybriefcase.getAmount()