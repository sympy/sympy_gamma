prepositions = ['of', 'to', 'for']
articles = ['the']
pronouns = ['me']
modifiers = {
    'tell': 'show',
    'show': 'show',
    'find': 'show',
    'how': 'how',
    'steps': 'how'
}
modifier_priorities = {
    'show': 0,
    'how': 1
}
commands = {
    'derivative': 'differentiate',
    'differentiate': 'differentiate'
}
functions = {
    'differentiate': {
        'show': 'diff',
        'how': 'diffsteps',
        'default': 'diff'
    }
}

def extraneous(word):
    return (word in prepositions) or (word in pronouns) or (word in articles)

def interpret(command):
    words = [word for word in command.lower().split() if not extraneous(word)]
    modifier = 'default'
    modifier_priority = -1
    cmds = []
    expressions = []
    expression = []

    for word in words:
        if word in modifiers:
            mod = modifiers[word]
            if modifier_priorities[mod] > modifier_priority:
                modifier = mod
                modifier_priority = modifier_priorities[mod]
            if expression:
                expressions.append(''.join(math))
        elif word in commands:
            cmds.append(commands[word])
            if expression:
                expressions.append(''.join(math))
        else:
            expression.append(word)
    if expression:
        expressions.append(' '.join(expression))
    for cmd in cmds:
        return functions[cmd][mod], expressions
