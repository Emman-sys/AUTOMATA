Set Expression Evaluator

Store sets of values under named variables.

Perform operations like:

concat → concatenate lists.

+ → union without duplicates.

|A| → get the length of a list or numeric value from a command.

Calculate prefixes of concatenated sequences.

Support interactive input with two phases:

Data input phase – store data in variables.

Command phase – evaluate expressions and see results.

Features
Custom Data Storage

Define variables in the format:

ini
Copy
Edit
A = 1,2,3
B = 4,5
Operations

Concatenation (concat):

css
Copy
Edit
A concat B   → [1,2,3,4,5]
Union without duplicates (+):

css
Copy
Edit
A + B        → [1,2,3,4,5]
Length (| ... |):

less
Copy
Edit
|A|          → 3
|A concat B| → 5
Prefix Calculation

Assign a prefix expression:

ini
Copy
Edit
prefix = A concat B
Outputs:

Copy
Edit
ε,1,12,123,1234,12345
Error Handling

Skips missing keys with an error message.

Ignores empty commands.

How It Works
Data Input Phase

The script first prompts:

pgsql
Copy
Edit
Enter rows in the format X= a,b,c (type 'done' to finish):
Enter data sets:

makefile
Copy
Edit
A = 1,2,3
B = 4,5
done
Command Phase

The script then asks:

bash
Copy
Edit
Enter command (e.g., A concat B) or 'exit':
Examples:

lua
Copy
Edit
A concat B
A + B
|A concat B|
prefix = A concat B
Prefix Output

If a prefix expression is set, the script will:

Display all possible prefixes including the empty string (ε).

Process after the prefix command or at the end.

Example Run
lua
Copy
Edit
Enter rows in the format X= a,b,c (type 'done' to finish):
A = 1,2,3
B = 4,5
done

Enter command (e.g., A concat B) or 'exit': A concat B
1,2,3,4,5

Enter command (e.g., A concat B) or 'exit': |A|
A = 1,2,3
3

Enter command (e.g., A concat B) or 'exit': prefix = A concat B
Prefix expression set to: A concat B
prefix = (A concat B)=
ε,1,12,123,1234,12345

Enter command (e.g., A concat B) or 'exit': exit
prefix = (A concat B)=
ε,1,12,123,1234,12345
File Structure
This is a single Python file. Key functions:

eval_concat(a, b) – joins two lists.

eval_plus(a, b) – joins lists without duplicates.

parse_command(cmd, suppress_print=False) – main expression parser.

flatten(lst) – flattens nested lists for prefix processing.

Requirements
Python 3.x

Runs entirely in the terminal.

No external libraries required (only re from the standard library).

Notes
Variables must be defined before use.

Commands are case-sensitive for variable names but case-insensitive for operators (concat, +).

Length (|...|) can be nested in expressions.
