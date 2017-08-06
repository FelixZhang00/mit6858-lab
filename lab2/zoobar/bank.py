from zoodb import *
from debug import *

import time

def transfer(sender, recipient, zoobars):
    persondb = person_setup()
    bankdb = bank_setup()
    senderp = bankdb.query(Bank).get(sender)
    recipientp = bankdb.query(Bank).get(recipient)

    if not senderp or not recipientp:
        return None

    sender_balance = senderp.zoobars - zoobars
    recipient_balance = recipientp.zoobars + zoobars

    if sender_balance < 0 or recipient_balance < 0:
        raise ValueError()

    senderp.zoobars = sender_balance
    recipientp.zoobars = recipient_balance
    bankdb.commit()

    transfer = Transfer()
    transfer.sender = sender
    transfer.recipient = recipient
    transfer.amount = zoobars
    transfer.time = time.asctime()

    transferdb = transfer_setup()
    transferdb.add(transfer)
    transferdb.commit()

def check_in(username):
    bankdb = bank_setup()
    user = bankdb.query(Bank).get(username)
    if user:
       return
 
    bank = Bank()
    bank.username = username
    bankdb.add(bank)
    bankdb.commit()


def balance(username):
    db = bank_setup()
    bank = db.query(Bank).get(username)
    if not bank:
        return None
    return bank.zoobars

def get_log(username):
    print "bank.py get_log username=%s" % username
    db = transfer_setup()
    # get the orm object,see:http://stackoverflow.com/questions/16450694/how-do-i-write-a-query-to-get-sqlalchemy-objects-from-relationship
    ret = db.query(Transfer).filter(or_(Transfer.sender==username,
                                         Transfer.recipient==username))
    retlist=[] 
    for item in ret:
        tt = {}
        tt['time']= item.time
        tt['sender'] = item.sender
        tt['recipient'] = item.recipient
        tt['amount'] = item.amount
        retlist.append(tt)            

    return retlist

