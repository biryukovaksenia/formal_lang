from collections import deque, defaultdict


def parse_regex(regex):
    i = 0
    elements = []

    while i < len(regex):
        char = regex[i]

        if char in "*+?":
            elements.append(('QUANTIFIER', char))
        elif char == "(":
            count_brackets = 1
            j = i + 1
            while j < len(regex) and count_brackets > 0:
                if regex[j] == "(":
                    count_brackets += 1
                elif regex[j] == ")":
                    count_brackets -= 1
                j += 1
            elements.append(('GROUP', parse_regex(regex[i + 1:j - 1])))
            i = j - 1
        elif char == "|":
            elements.append(('OR', char))
        elif char == "\\":
            if i + 1 < len(regex):
                elements.append(('SPECIAL', regex[i + 1]))
                i += 1
            else:
                elements.append(('LITERAL', char))
        else:
            elements.append(('LITERAL', char))
        i += 1

    return elements


class NFA:
    def __init__(self):
        self.transitions = {}  # (state, symbol) -> {states}
        self.initial_state = None
        self.final_states = set()

    def add_transition(self, start_state, symbol, end_state):
        if (start_state, symbol) not in self.transitions:
            self.transitions[(start_state, symbol)] = set()
        self.transitions[(start_state, symbol)].add(end_state)

    def set_initial_state(self, state):
        self.initial_state = state

    def add_final_state(self, state):
        self.final_states.add(state)


def regex_to_nfa(pattern):
    nfa = NFA()
    current_state = 0
    nfa.set_initial_state(current_state)

    def add_sequence(sequence, start_state):
        local_current = start_state
        for token in sequence:
            if token[0] == 'LITERAL':
                nfa.add_transition(local_current, token[1], local_current + 1)
                local_current += 1
            elif token[0] == 'QUANTIFIER':
                if token[1] == '+':
                    nfa.add_transition(local_current, '', local_current - 1)
                    local_current += 1
                    nfa.add_transition(local_current - 1, '', local_current)
                elif token[1] == '?':
                    nfa.add_transition(local_current, '', local_current + 1)
                    local_current += 1
                elif token[1] == '*':
                    nfa.add_transition(local_current, '', local_current - 1)
                    nfa.add_transition(local_current, '', local_current + 1)
                    local_current += 1
        return local_current

    for token in pattern:
        if token[0] == 'LITERAL':
            nfa.add_transition(current_state, token[1], current_state + 1)
            current_state += 1
        elif token[0] == 'GROUP':
            group_end = add_sequence(token[1], current_state)
            current_state = group_end
        elif token[0] == 'QUANTIFIER':
            if token[1] == '+':
                nfa.add_transition(current_state, '', current_state - 1)
                current_state += 1
                nfa.add_transition(current_state - 1, '', current_state)
            elif token[1] == '?':
                nfa.add_transition(current_state, '', current_state + 1)
                current_state += 1
            elif token[1] == '*':
                nfa.add_transition(current_state, '', current_state - 1)
                nfa.add_transition(current_state, '', current_state + 1)
                current_state += 1

    nfa.add_final_state(current_state)
    return nfa


def remove_epsilon_transitions(transition_dict):
    new_transitions = {}
    closures = {state: epsilon_closure(transition_dict, state) for state in set(s for s, _ in transition_dict)}

    for state, closure in closures.items():
        for inner_state in closure:
            for (src_state, symbol), dst_states in transition_dict.items():
                if src_state == inner_state and symbol != '':
                    if (state, symbol) not in new_transitions:
                        new_transitions[(state, symbol)] = set()
                    new_transitions[(state, symbol)].update(dst_states)

    return new_transitions


def nfa_to_dfa(transitions, initial_state, final_states_nfa):
    dfa = defaultdict(dict)
    initial_state_dfa = frozenset(
        epsilon_closure(transitions, initial_state))
    final_states_dfa = set()

    states = deque([initial_state_dfa])
    visited = {initial_state_dfa}

    while states:
        current = states.popleft()
        if any(state in final_states_nfa for state in current):
            final_states_dfa.add('-'.join(map(str, sorted(current))))

        for symbol in set(symbol for _, symbol in transitions if symbol):
            new_state = frozenset(set().union(*(epsilon_closure(transitions, state, symbol) for state in current)))
            if new_state:
                dfa['-'.join(map(str, sorted(current)))][symbol] = '-'.join(map(str, sorted(new_state)))
                if new_state not in visited:
                    visited.add(new_state)
                    states.append(new_state)

    return dfa, final_states_dfa


def epsilon_closure(transitions, state, symbol=None):
    closure = {state} if symbol is None else set()
    if symbol is not None:
        if (state, symbol) in transitions:
            closure |= transitions[(state, symbol)]

    stack = list(closure)
    while stack:
        current_state = stack.pop()
        for next_state in transitions.get((current_state, ''), []):
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)
    return closure


def matches_dfa(dfa, input_string, final_states):
    current_state = '0'  # Начинаем с начального состояния
    for symbol in input_string:
        if symbol in dfa.get(current_state, {}):
            current_state = dfa[current_state][symbol]
        else:
            return False  # Нет перехода для текущего символа

    return current_state in final_states


if __name__ == "__main__":
    regex = "a+b+c"
    test_strings = ['aaabbc', 'aaaaaa', 'aabbbd', 'abbbbcdddddd']
    parsed_regex = parse_regex(regex)
    print("Parsed regex:", parsed_regex)

    nfa = regex_to_nfa(parsed_regex)
    print("NFA Transitions:", dict(nfa.transitions))
    print("Initial state:", nfa.initial_state)
    print("Final states:", nfa.final_states)

    nfa_without_epsilon = remove_epsilon_transitions(nfa.transitions)
    print("NFA without epsilon transitions:", nfa_without_epsilon)

    print(nfa.initial_state)
    print(nfa.final_states)
    dfa, final_state = nfa_to_dfa(nfa_without_epsilon, nfa.initial_state, nfa.final_states)

    results = {s: matches_dfa(dfa, s, final_state) for s in test_strings}
    print("DFA:", results)

