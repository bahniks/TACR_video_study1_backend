round: 3-6
offer: "|".join(["outcome", str(wins), str(reward), self.condition])


round: "token"
offer: True/False


round: 3-6
offer: "outcome"
response: "|".join(["outcome", str(otherwins), str(otherreward), otherversion]) + "_True"


round: 0
offer: "login"
                    condition = random.choice(["control", "version", "reward", "version_reward"])
                    incentive_order = random.choice(["high-low", "low-high"])
                    tokenCondition = random.choice([True, False])                    
                    winning_block = str(random.randint(1,6))
                    winning_trust = str(random.randint(3,6))
                    trustRoles = "".join([random.choice(["A", "B"]) for i in range(4)])
                    trustPairs = "_".join([str(random.randint(1, 10)) for i in range(4)])  
response: "|".join(["start", condition, incentive_order, str(tokenCondition), winning_block, winning_trust, trustRoles, trustPairs])


'round': "trust" + str(self.root.status["trustblock"])
'offer': "_".join([self.frames[i].valueVar.get() for i in range(7)])


round: 3-6
offer: "trust"
response: "_".join(map(str, [self.root.status["trust_pairs"][block - 1], sentA, sentB]))


