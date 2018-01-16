import hashlib
import json
from time import time
from uuid import uuid4
import requests
from urllib.parse import urlparse


class Blockchain(object):

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.newBlock(previous_hash=1, proof=100)
        

    def registerNode(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def newBlock(self, proof, previous_hash=None):

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def newTransaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.lastBlock['index'] + 1

    @staticmethod
    def hash(block):

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def lastBlock(self):

        return self.chain[-1]

    def proofOfWork(self, last_proof):

        proof = 0

        while self.validProof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def validProof(last_proof, proof):

        guess = str(last_proof * proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    def validChain(self, chain):

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n======================================\n")
            # 이전 블럭 검사
            if block['previous_hash'] != self.hash(last_block):
                return False
            # 블럭 검증
            if not self.validProof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
            
        return True

    def resolveConflicts(self):

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get('http://{%s}/chain'%(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.validChain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False