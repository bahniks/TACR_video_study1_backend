def generate_rounds(ps):
    used_pairs = set()
    all_pairings = list(itertools.combinations(ps, 2))      
    round_pairings = {x:[] for x in range(3,7)}
    try:  
        for r in range(4, 7):        
            available_pairings = [pair for pair in all_pairings if pair not in used_pairs]
            random.shuffle(available_pairings)
            used_participants = set()
            for _ in range(len(ps) // 2):                                                            
                pair = available_pairings.pop(0)                 
                round_pairings[r].append(pair)
                used_pairs.add(pair)
                used_participants.add(pair[0])
                used_participants.add(pair[1])
                available_pairings = [pair for pair in available_pairings if pair[0] not in used_participants and pair[1] not in used_participants]
        return round_pairings        
    except IndexError:
        return(generate_rounds(ps))


def generate_third(unused_pairs, participants):        
    round_pairings = []
    available_pairings = unused_pairs
    try:                   
        random.shuffle(unused_pairs)
        used_participants = set()
        for _ in range(len(participants) // 2):
            pair = available_pairings.pop(0)                 
            round_pairings.append(pair)
            used_participants.add(pair[0])
            used_participants.add(pair[1])
            available_pairings = [pair for pair in available_pairings if pair[0] not in used_participants and pair[1] not in used_participants]
        return round_pairings
    except IndexError:
        return(generate_third(unused_pairs, participants))   