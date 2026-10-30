import sys
from .scorer import Scorer
if len(sys.argv) != 3:
    sys.exit('usage: python -m prompt_guess_scoring "<answer>" "<guess>"')
print(Scorer().score(sys.argv[1], sys.argv[2]))
