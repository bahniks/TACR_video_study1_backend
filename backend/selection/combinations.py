import itertools
import random

def generate_rounds(ps, check = False):
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

        if check:
            all_pairings = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in all_pairings]
            used_pairs = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in used_pairs]
            unused_pairs = list(set(all_pairings) - set(used_pairs))
            try:
                generate_third(unused_pairs, ps)
            except Exception:
                return(generate_rounds(ps, check = True))
            else:
                return round_pairings
        else: 
            return round_pairings
    except IndexError:
        return(generate_rounds(ps))


def generate_third(unused_pairs, participants):        
    round_pairings = []
    available_pairings = unused_pairs.copy()
    try:                   
        random.shuffle(available_pairings)
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



if __name__ == "__main__":
    for i in range(100):        
        try:
            participants = [i for i in range(6)]
            random.shuffle(participants)
            if len(participants) % 2 != 0:
                removed = participants.pop()
            round_pairings = {x:[] for x in range(3,7)}
            num_groups = len(participants) // 4
            for i in range(num_groups):
                if i == num_groups - 1:
                    ps = participants[slice(4*i, len(participants))]
                else:
                    ps = participants[slice(4*i, 4*i+4)]
                condition = random.choice(["control", "version", "reward", "version_reward"])
                reward_order = random.choice(["high-low", "low-high"])      
                for r, pairs in generate_rounds(ps).items():
                    round_pairings[r].extend(pairs)     
            all_pairings = list(itertools.combinations(participants, 2))  
            all_pairings = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in all_pairings]
            used_pairs = [x for xs in round_pairings.values() for x in xs]
            used_pairs = [(i[0], i[1]) if i[0] < i[1] else (i[1], i[0]) for i in used_pairs]
            unused_pairs = list(set(all_pairings) - set(used_pairs))
            round_pairings[3] = generate_third(unused_pairs, participants)
        except Exception as e:
            print(e)
        else:
            print(round_pairings)

