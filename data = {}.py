data = {}

prefix_expr = None
suffix_expr = None

import re

# Helpers to normalize expressions
def _strip_outer_parens(s: str) -> str:
    s = s.strip()
    # Remove balanced outer parentheses repeatedly
    while s.startswith('(') and s.endswith(')'):
        bal = 0
        outer_covers_all = False
        for i, ch in enumerate(s):
            if ch == '(': bal += 1
            elif ch == ')':
                bal -= 1
                if bal == 0:
                    outer_covers_all = (i == len(s) - 1)
                    break
        if outer_covers_all:
            s = s[1:-1].strip()
        else:
            break
    return s

# Flatten helper reused by post-phase printers
def flatten_list(lst):
    for x in lst:
        if isinstance(x, list):
            yield from flatten_list(x)
        else:
            yield str(x)

# Input phase
print("Enter rows in the format X= a,b,c (type 'done' to finish):")
while True:
    line = input()
    if line.strip().lower() == 'done':
        break
    # Check for prefix command
    if line.strip().lower().startswith('prefix'):
        eq_idx = line.find('=')
        if eq_idx != -1:
            expr = line[eq_idx+1:].strip()
            prefix_expr = _strip_outer_parens(expr)
        continue
    # Check for suffix command
    if line.strip().lower().startswith('suffix'):
        eq_idx = line.find('=')
        if eq_idx != -1:
            expr = line[eq_idx+1:].strip()
            suffix_expr = _strip_outer_parens(expr)
        continue
    if '=' in line:
        key, values = line.split('=', 1)
        key = key.strip()
        # Filter out empty strings caused by trailing commas
        values = [v.strip() for v in values.strip().split(',') if v.strip()]
        data[key] = values

def eval_concat(a, b):
    # a and b can be either a key in data, a temporary list, or a digit string
    if isinstance(a, list):
        left = a
    elif isinstance(a, str) and a.isdigit():
        left = [a]
    else:
        left = data.get(a)
    if isinstance(b, list):
        right = b
    elif isinstance(b, str) and b.isdigit():
        right = [b]
    else:
        right = data.get(b)
    if left is not None and right is not None:
        return left + right
    return None

def eval_plus(a, b):
    # a and b can be either a key in data, a temporary list, or a digit string
    if isinstance(a, list):
        left = a
    elif isinstance(a, str) and a.isdigit():
        left = [a]
    else:
        left = data.get(a)
    if isinstance(b, list):
        right = b
    elif isinstance(b, str) and b.isdigit():
        right = [b]
    else:
        right = data.get(b)
    if left is not None and right is not None:
        result = []
        seen = set()
        for x in left + right:
            if x not in seen:
                result.append(x)
                seen.add(x)
        return result
    return None

 

def parse_command(cmd, suppress_print=False):
    cmd = _strip_outer_parens(cmd)
    # Handle palindrome operator: P(<expr>) checks if evaluated string is a palindrome
    m_pal = re.fullmatch(r"[pP]\s*\((.*)\)", cmd)
    if m_pal:
        inner = m_pal.group(1).strip()
        inner_result = parse_command(inner, suppress_print=True)
        if isinstance(inner_result, list):
            s = ''.join(flatten_list(inner_result))
        elif isinstance(inner_result, str):
            s = inner_result
        else:
            # Treat inner as a literal when it doesn't parse to a value
            s = inner
        is_pal = (s == s[::-1])
        out = 'palindrome' if is_pal else 'not palindrome'
        if not suppress_print:
            print(out)
        return out
    # Handle reverse operator: r(<expr>) reverses the evaluated sequence
    m_rev = re.fullmatch(r"[rR]\s*\((.*)\)", cmd)
    if m_rev:
        inner = m_rev.group(1).strip()
        inner_result = parse_command(inner, suppress_print=True)
        if isinstance(inner_result, list):
            rev_list = list(reversed(inner_result))
            if not suppress_print:
                print(','.join(rev_list))
            return rev_list
        elif isinstance(inner_result, str):
            # If a string is returned (e.g., from a length expression), reverse characters
            rev_chars = list(reversed(list(inner_result)))
            if not suppress_print:
                print(','.join(rev_chars))
            return rev_chars
        else:
            if not suppress_print:
                print("Invalid command.")
            return None
    # Helper: recursively replace all |...| with their lengths
    def eval_bars(s):
        bar_pattern = r'\|([^|]+)\|'
        while re.search(bar_pattern, s):
            def repl(m):
                inner_cmd = m.group(1).strip()
                inner_res = parse_command(inner_cmd, suppress_print=True)
                if isinstance(inner_res, list):
                    return str(len(inner_res))
                elif isinstance(inner_res, str) and inner_res.isdigit():
                    return str(int(inner_res))
                else:
                    return '0'
            s = re.sub(bar_pattern, repl, s)
        return s

    # Pretty print only for top-level single bar expressions
    if re.fullmatch(r'\|\s*[^|]+\s*\|', cmd):
        inner_cmd = cmd[1:-1].strip()
        inner_result = parse_command(inner_cmd, suppress_print=True)
        if isinstance(inner_result, list):
            if not suppress_print:
                print(f"{inner_cmd} = {','.join(inner_result)}")
                print(len(inner_result))
            return str(len(inner_result))
        elif isinstance(inner_result, str) and inner_result.isdigit():
            if not suppress_print:
                print(f"{inner_cmd} = {inner_result}")
                print(inner_result)
            return inner_result
        else:
            if not suppress_print:
                print(f"{inner_cmd} = 0")
                print('0')
            return '0'

    replaced = eval_bars(cmd)

    # Tokenize while respecting parentheses, so r(A concat B) stays one token
    def tokenize(s: str):
        tokens = []
        cur = []
        depth = 0
        for ch in s:
            if ch == '(':
                depth += 1
                cur.append(ch)
            elif ch == ')':
                depth -= 1
                cur.append(ch)
            elif ch.isspace() and depth == 0:
                if cur:
                    tokens.append(''.join(cur))
                    cur = []
            else:
                cur.append(ch)
        if cur:
            tokens.append(''.join(cur))
        return [t.strip() for t in tokens if t.strip()]

    tokens = tokenize(replaced)

    # Evaluate an operand token into a list (or None on missing key)
    def eval_operand(tok):
        t = tok.strip()
        # reverse operator as operand
        m = re.fullmatch(r"[rR]\s*\((.*)\)", t)
        if m:
            inner = m.group(1).strip()
            res = parse_command(inner, suppress_print=True)
            if isinstance(res, list):
                return list(reversed(res))
            if isinstance(res, str) and res.isdigit():
                return [res]
            return None
        # parenthesized sub-expression
        if t.startswith('(') and t.endswith(')'):
            inner = t[1:-1].strip()
            res = parse_command(inner, suppress_print=True)
            if isinstance(res, list):
                return res
            if isinstance(res, str) and res.isdigit():
                return [res]
            return None
        # digits
        if t.isdigit():
            return [t]
        # key lookup
        return data.get(t)
    if len(tokens) >= 1:
        if len(tokens) == 1:
            res = eval_operand(tokens[0])
            if res is not None:
                if not suppress_print:
                    print(','.join(res))
                return res
            else:
                if not suppress_print:
                    print(tokens[0])
                return [tokens[0]]
        if len(tokens) == 2 and tokens[1].isdigit():
            left = eval_operand(tokens[0])
            if left is not None:
                if not suppress_print:
                    print(','.join(left) + ' ' + tokens[1])
                return left + [tokens[1]]
            else:
                if not suppress_print:
                    print(tokens[0] + ' ' + tokens[1])
                return [tokens[0], tokens[1]]
        if len(tokens) >= 3:
            # Handle trailing digit append
            if tokens[-1].isdigit() and len(tokens) >= 4 and len(tokens) % 2 == 0:
                valid = all(tokens[i].lower() == 'concat' or tokens[i] == '+' for i in range(1, len(tokens)-2, 2))
                if valid:
                    current = eval_operand(tokens[0])
                    if current is None:
                        if not suppress_print:
                            print("One of the keys does not exist.")
                        return None
                    for i in range(1, len(tokens)-2, 2):
                        op = tokens[i]
                        right = eval_operand(tokens[i+1])
                        if right is None:
                            if not suppress_print:
                                print("One of the keys does not exist.")
                            return None
                        if op.lower() == 'concat':
                            current = current + right
                        elif op == '+':
                            merged = []
                            seen = set()
                            for x in current + right:
                                if x not in seen:
                                    merged.append(x)
                                    seen.add(x)
                            current = merged
                    if not suppress_print:
                        print(','.join(current) + ' ' + tokens[-1])
                    return current + [tokens[-1]]
            # Normal alternating operand-operator-operand pattern
            if len(tokens) % 2 == 1:
                valid = all(tokens[i].lower() == 'concat' or tokens[i] == '+' for i in range(1, len(tokens)-1, 2))
                if valid:
                    current = eval_operand(tokens[0])
                    if current is None:
                        if not suppress_print:
                            print("One of the keys does not exist.")
                        return None
                    for i in range(1, len(tokens), 2):
                        op = tokens[i]
                        right = eval_operand(tokens[i+1])
                        if right is None:
                            if not suppress_print:
                                print("One of the keys does not exist.")
                            return None
                        if op.lower() == 'concat':
                            current = current + right
                        elif op == '+':
                            merged = []
                            seen = set()
                            for x in current + right:
                                if x not in seen:
                                    merged.append(x)
                                    seen.add(x)
                            current = merged
                    if not suppress_print:
                        print(','.join(current))
                    return current
    if not suppress_print:
        print("Invalid command.")
    return None

# Command phase
while True:
    cmd = input("Enter command (e.g., A concat B) or 'exit': ")
    if cmd.strip().lower() == 'exit':
        break
    # Allow prefix assignment in command phase
    if cmd.strip().lower().startswith('prefix'):
        eq_idx = cmd.find('=')
        if eq_idx != -1:
            raw_expr = cmd[eq_idx+1:].strip()
            prefix_expr = _strip_outer_parens(raw_expr)
            print(f"Prefix expression set to: {prefix_expr}")
            # Immediately show the prefix answer after setting
            print("prefix = (" + prefix_expr + ")=")
            result = parse_command(prefix_expr, suppress_print=True)
            if isinstance(result, list):
                s = ''.join(result)
                prefixes = ['ε']
                for i in range(1, len(s)+1):
                    prefixes.append(s[:i])
                print(','.join(prefixes))
            else:
                print('empty')
        continue
    # Allow suffix assignment in command phase
    if cmd.strip().lower().startswith('suffix'):
        eq_idx = cmd.find('=')
        if eq_idx != -1:
            raw_expr = cmd[eq_idx+1:].strip()
            suffix_expr = _strip_outer_parens(raw_expr)
            print(f"Suffix expression set to: {suffix_expr}")
            # Immediately show the suffix answer after setting
            print("suffix = (" + suffix_expr + ")=")
            result = parse_command(suffix_expr, suppress_print=True)
            if isinstance(result, list):
                s = ''.join(result)
                # Generate suffixes shortest->longest, then place epsilon at the end
                suffixes = [s[-i:] for i in range(1, len(s)+1)] + ['ε']
                print(','.join(suffixes))
            else:
                print('ε')
        continue
    # Skip empty commands (don't print "Invalid command.")
    if not cmd.strip():
        continue
    parse_command(cmd)

# After command phase, process prefix if set
if prefix_expr:
    print("prefix = (" + _strip_outer_parens(prefix_expr) + ")=")
    result = parse_command(prefix_expr, suppress_print=True)
    if isinstance(result, list):
        s = ''.join(flatten_list(result))
        # Debug print to check what s is
        # print(f"DEBUG: s = '{s}'")
        if s.strip():  # Check if s is not just whitespace or empty
            prefixes = ['ε'] + [s[:i] for i in range(1, len(s)+1)]
            print(','.join(prefixes))
        else:
            print('empty')
    else:
        print('empty')

# After command phase, process suffix if set
if suffix_expr:
    print("suffix = (" + _strip_outer_parens(suffix_expr) + ")=")
    result = parse_command(suffix_expr, suppress_print=True)
    if isinstance(result, list):
        s = ''.join(flatten_list(result))
        if s.strip():
            # Put epsilon at the end for suffix output
            suffixes = [s[-i:] for i in range(1, len(s)+1)] + ['ε']
            print(','.join(suffixes))
        else:
            print('empty')
    else:
        print('empty')