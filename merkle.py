# Python hash signature library (quantum resistant)
#
# creates merkle trees for the MSS incorporating either lamport or winternitz OTS.

# creates winternitz OTS key pairs, signs and verifies a winternitz one time signature. 
# creates lamport-diffie OTS key pairs, signs and verifies a lamport one time signature.
#
# todo first: WOTS+, alter merkle trees to use an XOR bitmask (do not require underlying hash function to be collision resistant)
# 
# todo: full implementation of Winternitz+, IETF Hash-Based Signatures draft-mcgrew-hash-sigs-02 LDWM scheme,
# GMSS and XMSS.


__author__ = 'pete'
from bitcoin import sha256
from bitcoin import random_key
from binascii import unhexlify
from math import ceil, floor, log
import time
import random




def numlist(array):
    for a,b in enumerate(array):
        print a,b
    return


# winternitz ots+               #need to generate a seed from PRF to populate sk_1->sk_l1, r and k. Otherwise need the public key and private key to sign..

def fn_k(x,k):
    return sha256(k+x)

def chain_fn(x,r,i,k):
    if i == 0:
        return x
    else:
        for y in range(i):
            x = fn_k(hex(int(x,16)^int(r[y],16)),k)
    return x

def chain_fn2(x,r,i,k):
        for y in range(i,15):
            x = fn_k(hex(int(x,16)^int(r[y],16)),k)
        return x


def random_wpkey(w=16):

    # first calculate l_1 + l_2 = l .. see whitepaper http://theqrl.org/whitepaper/QRL_whitepaper.pdf
    # if using SHA-256 then m and n = 256

    m = 256
    l_1 = ceil(m/log(w,2))
    l_2 = floor(log((l_1*(w-1)),2)/log(w,2)) + 1
    l = int(l_1+l_2)

    sk = []
    pub = []

    # next create l+w-1 256 bit secret key fragments..(we will update this to use a PRF instead of random_key)
    # l n-bits will be private key, remaining w-1 will be r, the randomisation elements for the chaining function
    # finally generate k the key for the chaining function..

    for x in range(l+w-1):
        sk.append(random_key())

    priv = sk[:-(w-1)]
    r = sk[l:]

    k = random_key()

    pub.append((r,k))       #pk_0 = (r,k) ..where r is a list of w-1 randomisation elements

    for sk_ in priv:
        pub.append(chain_fn(sk_,r,w-1,k))

    return priv, pub


def sign_wpkey(priv, message, pub, w=16):            

    m = 256
    if w==16:
        l_1 = 64
        l_2 = 3
        l = 67
    else:    
        l_1 = ceil(m/log(w,2))
        l_2 = floor(log((l_1*(w-1)),2)/log(w,2)) + 1
        l = int(l_1+l_2)

    message = sha256(message)       #outputs 256 bit -> 64 hexadecimals. each hex digit is therefore 4 bits..

    s = []
    checksum = 0

    for x in range(int(l_1)):
        y = int(message[x],16)
        s.append(y)
        checksum += w-1-y

    c = (hex(checksum))[2:]

    if len(c) < 3:
        c = '0'+c

    for x in range(int(l_2)):
        y = int(c[x],16)
        s.append(y)

    signature = []

    for x in range(int(l)):         #merkle.chain_fn(priv[0],pub[0][0],15,pub[0][1])
        signature.append(chain_fn(priv[x],pub[0][0],s[x],pub[0][1]))

    return signature

def verify_wpkey(signature, message, pub, w=16):
    m = 256
    if w==16:
        l_1 = 64
        l_2 = 3
        l = 67
    else:    
        l_1 = ceil(m/log(w,2))
        l_2 = floor(log((l_1*(w-1)),2)/log(w,2)) + 1
        l = int(l_1+l_2)

    message = sha256(message)

    s = []
    checksum = 0

    for x in range(int(l_1)):
        y = int(message[x],16)
        s.append(y)
        checksum += w-1-y

    c = (hex(checksum))[2:]

    if len(c) < 3:
        c = '0'+c

    for x in range(int(l_2)):
        y = int(c[x],16)
        s.append(y)

    pub2 = []

    for x in range(int(l)):         #merkle.chain_fn(priv[0],pub[0][0],15,pub[0][1])
        pub2.append(chain_fn2(signature[x],pub[0][0],s[x],pub[0][1]))

    if pub2 == pub[1:]:
        return True

    return False

# winternitz ots

def random_wkey(w=8, verbose=0):      #create random W-OTS keypair
    # Use F = SHA256/SHA512 and G = SHA256/512
    if w > 16:
        w = 16      #too many hash computations to make this sensible.  16 = 3.75s, 8 = 0.01s 1024 bytes..
    priv = []
    pub = []
    start_time = time.time()
    for x in range(256/w):
        a = random_key()
        priv.append(a)
        for y in range(2**w-1):              #F
            a = sha256(a)
        pub.append(sha256(a))               #G (just in case we have a different f from g).

    elapsed_time = time.time() - start_time
    if verbose == 1:
        print elapsed_time
    return priv, pub    

def temp():
    priv = random_key()
    pub = priv
    for x in range(256):
        pub = sha256(pub)
    message = 'h'

    return priv, pub, message

def sign_wkey(priv, message):      #only works with 8 at present. havent separated the 'g' component yet.

    signature = []
    bin_msg = unhexlify(sha256(message))

    for y in range(len(priv)):
        s = priv[y]    
        for x in range(256-ord(bin_msg[y:y+1])):
            s = sha256(s)
        signature.append(s)
    return signature

def verify_wkey(signature, message, pub):

    verify = []
    bin_msg = unhexlify(sha256(message))
    
    for x in range(len(signature)):
        a = signature[x]
                                                    #f is all but last hash..
        for z in range(ord(bin_msg[x:x+1])):
                a=sha256(a)
        #a = sha256(a)                               #g is the final hash, separate so can be changed..
        verify.append(a)
  
    if pub != verify:
        return False

    return True


# lamport-diffie ots

def sign_lkey(priv, message):       #perform lamport signature
    
    signature = [] 
    bin_lmsg = unhexlify(sha256(message))

    z = 0
    for x in range (len(bin_lmsg)):
        l_byte = bin(ord(bin_lmsg[x]))[2:] #[2:][-1:]      #generate a binary string of 8 bits for each byte of 32/256.
        
        while len(l_byte) < 8:               #pad the zero's up to 8
                l_byte = '0'+ l_byte
        
        for y in range(0,8):
         if l_byte[-1:] == '0':
            signature.append(priv[z][0])
            l_byte = l_byte[:-1]
            z+=1
         else:
            signature.append(priv[z][1])
            l_byte = l_byte[:-1]
            z+=1

    return signature


def verify_lkey(signature, message, pub ):  #verify lamport signature

    bin_lmsg = unhexlify(sha256(message))
    verify = []
    z = 0

    for x in range (len(bin_lmsg)):
        l_byte = bin(ord(bin_lmsg[x]))[2:]   #generate a binary string of 8 bits for each byte of 32/256.
        
        while len(l_byte) < 8:               #pad the zero's up to 8
                l_byte = '0'+ l_byte
        
        for y in range(0,8):
         if l_byte[-1:] == '0':
            verify.append((sha256(signature[z]),pub[z][0]))
            l_byte = l_byte[:-1]
            z+=1
         else:
            verify.append((sha256(signature[z]),pub[z][1]))
            l_byte = l_byte[:-1]
            z+=1

    for p in range(len(verify)):
        if verify[p][0] == verify[p][1]:
            pass
        else:
            return False    

    return True

def random_lkey(numbers=256):      #create random lamport signature scheme keypair

    priv = []
    pub = []

    for x in range (numbers):
        a,b = random_key(), random_key()
        priv.append((a,b))
        pub.append((sha256(a),sha256(b)))

    return priv, pub

# merkle signature scheme

def verify_mss(sig, data, message, ots_key=0):       #verifies that the sig is generated from pub..for now need to specify keypair..

    if not sig:
        return False

    if not message:
        return False

    if ots_key > len(data)-1:
        raise Exception('OTS key higher than available signatures')

    if data[0].type == 'WOTS':
        return verify_wkey(sig, message, data[ots_key].pub)
    elif data[0].type == 'LDOTS':
        return verify_lkey(sig, message, data[ots_key].pub)

def verify_root(pub, merkle_root, merkle_path):

    if not pub:
        return False
    if not merkle_root:
        return False
    if not merkle_path:
        return False

    if len(pub) == 256:             #then LDOTS, need to add this to correctly concat the pub->pubhash
        pub = [i for sub in pub for i in sub] 

    pubhash = sha256(''.join(pub))

    if pubhash not in merkle_path[0]:
        print 'hashed public key not in merkle path'
        return False

    for x in range(len(merkle_path)):
        if len(merkle_path[x]) == 1:
            if ''.join(merkle_path[x]) == merkle_root:
                return True
            else:
                print 'root check failed'
                return False
        if sha256(merkle_path[x][0]+merkle_path[x][1]) not in merkle_path[x+1]:
                return False
                print 'path authentication error'

    return False
    

def sign_mss(data, message, ots_key=0):
    
    if not data:
        return False

    if not message:
        return False

    if ots_key > len(data)-1:
        raise Exception('OTS key number greater than available signatures')
        return False

    if data[0].type == 'WOTS':
        return sign_wkey(data[ots_key].priv, message)
    elif data[0].type == 'LDOTS':
        return sign_lkey(data[ots_key].priv, message)

# winternitz merkle signature scheme 

def random_wmss(signatures=4, verbose=0):  #create a w-ots mms with multiple signatures..
    begin = time.time()
    data = []
    pubhashes = []

    for x in range(signatures):
        data.append(WOTS(signatures, index=x, verbose=verbose ))

    for i in range(len(data)):
        pubhashes.append(data[i].pubhash)

    a = Merkle(base=pubhashes,verbose=verbose)

    for y in range(signatures):
        data[y].merkle_root = ''.join(a.root)
        data[y].merkle_path = a.auth_lists[y]
        data[y].merkle_obj = a

    if verbose == 1:
        print 'Total MSS time = ',str(time.time()-begin)

    return data                 #array of wots classes full of data.. and a class full of merkle

# lamport-diffie merkle signature scheme

def random_ldmss(signatures=4, verbose=0):
    begin = time.time()
    data = []
    pubhashes = []

    for x in range(signatures):
        data.append(LDOTS(signatures, index=x, verbose=verbose))

    for i in range(len(data)):
        pubhashes.append(data[i].pubhash)

    a = Merkle(base=pubhashes, verbose=verbose)

    for y in range(signatures):
        data[y].merkle_root = ''.join(a.root)
        data[y].merkle_path = a.auth_lists[y]
        data[y].merkle_obj = a
    if verbose == 1:
        print 'Total MSS time = ',str(time.time()-begin)

    return data                




class LDOTS():
    def __init__(self, signatures, index=0,verbose=0):
        self.signatures = signatures
        self.merkle_obj = []
        self.merkle_root = ''
        self.merkle_path = []
        self.state = 0
        self.type = 'LDOTS'
        self.index = index
        self.concatpub = ""
        if verbose == 1:
            print 'New LD keypair generation ', str(self.index)
        self.priv, self.pub = random_lkey()
        
        self.publist = [i for sub in self.pub for i in sub]    #convert list of tuples to list to allow cat.    
        self.concatpub = ''.join(self.publist)
        self.pubhash = sha256(self.concatpub)
        return

    def screen_print(self):
        print numlist(self.priv)
        print numlist(self.pub)
        print self.concatpub
        print self.pubhash
        return

class WOTS():
    def __init__(self, signatures, index=0, verbose=0):
        self.signatures = signatures
        self.merkle_obj = []
        self.merkle_root = ''
        self.merkle_path = []
        self.state = 0
        self.type = 'WOTS'
        self.index = index
        self.concatpub = ""
        if verbose == 1:
            print 'New W-OTS keypair generation ', str(self.index)
        self.priv, self.pub = random_wkey(verbose=verbose)
                
        self.concatpub = ''.join(self.pub)
        self.pubhash = sha256(self.concatpub)
        return

    def screen_print(self):
        print numlist(self.priv)
        print numlist(self.pub)
        print self.concatpub
        print self.pubhash
        return

# merkle tree creation

class Merkle():

 def __init__(self, base=[], verbose=0):
    self.base = base
    self.verbose = verbose
    self.tree = []
    self.num_leaves = len(self.base)
    if not self.base:
        return
    else:
        self.create_tree()
        self.route_proof()


 def route_proof(self):             #need to add in error detection..
    start_time = time.time()
    self.auth_lists = []
    
    if self.verbose == 1:
        print 'Calculating proofs: tree height ',str(self.height), ',',str(self.num_leaves) ,' leaves'

    for y in range(self.num_leaves):
        auth_route = []
        leaf = self.tree[0][y]
        for x in range(self.height):      
            if len(self.tree[x])==1:    
                if self.tree[x] == self.root:       
                    auth_route.append(self.root)    
                    self.auth_lists.append(auth_route)
                else:
                    print 'Merkle route calculation failed @ root'   
            else:
                nodes = self.tree[x]
                nodes_above = self.tree[x+1]      
                for node in nodes:          
                    if leaf != node:
                        for nodehash in nodes_above:
                            if sha256(leaf+node) == nodehash:
                                auth_route.append((leaf, node))         #binary hash is ordered
                                leaf = nodehash
                            elif sha256(node+leaf) == nodehash:
                                auth_route.append((node,leaf))
                                leaf = nodehash
                            else:
                                pass
    elapsed_time = time.time() - start_time
    if self.verbose ==1:
        print elapsed_time   
    
    return

 def create_tree(self):

    if self.num_leaves <= 2:
        num_branches = 1
    elif self.num_leaves >2 and self.num_leaves <=4:
        num_branches = 2
    elif self.num_leaves >4 and self.num_leaves <=8:
        num_branches = 3
    elif self.num_leaves >8 and self.num_leaves <=16:
        num_branches = 4
    elif self.num_leaves >16 and self.num_leaves <=32:
        num_branches = 5
    elif self.num_leaves >32 and self.num_leaves <=64:
        num_branches = 6
    elif self.num_leaves >64 and self.num_leaves <=128:
        num_branches = 7
    elif self.num_leaves >128 and self.num_leaves <=256:
        num_branches = 8
    elif self.num_leaves >256 and self.num_leaves <=512:
        num_branches = 9

    self.num_branches = num_branches
    self.tree.append(self.base)

    hashlayer = self.base

    for x in range(num_branches):       #iterate through each layer of the merkle tree starting with the base layer
        temp_array = []
        cycles = len(hashlayer)%2 + len(hashlayer)/2
        y = 0
        for x in range(cycles):
            if y+1 == len(hashlayer):
             temp_array.append(str(hashlayer[y]))
            else:
             temp_array.append(sha256(str(hashlayer[y])+str(hashlayer[y+1])))
             y=y+2

        self.tree.append(temp_array)
        hashlayer = temp_array
    self.root = temp_array
    self.height = len(self.tree)
    if self.verbose==1:
        print 'Merkle tree created with '+str(self.num_leaves),' leaves, and '+str(self.num_branches)+' to root.'
    return self.tree

 def check_item(self):
     return