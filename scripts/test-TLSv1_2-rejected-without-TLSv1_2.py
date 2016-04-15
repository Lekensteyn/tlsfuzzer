# Author: Hubert Kario, (c) 2016
# Released under Gnu GPL v2.0, see LICENSE file for details

"""Minimal test for verifying DHE_RSA key exchange support"""

from __future__ import print_function
import traceback
import sys

from tlsfuzzer.runner import Runner
from tlsfuzzer.messages import Connect, ClientHelloGenerator, \
        ClientKeyExchangeGenerator, ChangeCipherSpecGenerator, \
        FinishedGenerator, ApplicationDataGenerator, AlertGenerator
from tlsfuzzer.expect import ExpectServerHello, ExpectCertificate, \
        ExpectServerHelloDone, ExpectChangeCipherSpec, ExpectFinished, \
        ExpectAlert, ExpectClose, \
        ExpectApplicationData

from tlslite.constants import CipherSuite, AlertLevel, AlertDescription, \
        ExtensionType

def main():
    """Test if server supports the DHE_RSA key exchange"""
    conversations = {}

    # sanity check
    conversation = Connect("localhost", 4433)
    node = conversation
    ciphers = [CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA]
    node = node.add_child(ClientHelloGenerator(ciphers,
                                               extensions={ExtensionType.
                                                   renegotiation_info:None}))
    node = node.add_child(ExpectServerHello(version=(3, 3),
                                            extensions={ExtensionType.
                                                     renegotiation_info:None}))
    node = node.add_child(ExpectCertificate())
    #node = node.add_child(ExpectServerKeyExchange())
    node = node.add_child(ExpectServerHelloDone())
    node = node.add_child(ClientKeyExchangeGenerator())
    node = node.add_child(ChangeCipherSpecGenerator())
    node = node.add_child(FinishedGenerator())
    node = node.add_child(ExpectChangeCipherSpec())
    node = node.add_child(ExpectFinished())
    node = node.add_child(ApplicationDataGenerator(
        bytearray(b"GET / HTTP/1.0\n\n")))
    node = node.add_child(ExpectApplicationData())
    node = node.add_child(AlertGenerator(AlertLevel.warning,
                                         AlertDescription.close_notify))
    node = node.add_child(ExpectAlert())
    node.next_sibling = ExpectClose()

    conversations["sanity check"] = conversation

    # check TLSv1.2 ciphers without TLSv1.2 client hello
    for cipher in [CipherSuite.TLS_DHE_RSA_WITH_AES_128_CBC_SHA256,
                   CipherSuite.TLS_DHE_RSA_WITH_AES_256_CBC_SHA256,
                   CipherSuite.TLS_DHE_RSA_WITH_AES_128_GCM_SHA256,
                   CipherSuite.TLS_DHE_RSA_WITH_AES_256_GCM_SHA384,
                   CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA256,
                   CipherSuite.TLS_RSA_WITH_AES_256_CBC_SHA256,
                   CipherSuite.TLS_RSA_WITH_AES_128_GCM_SHA256,
                   CipherSuite.TLS_RSA_WITH_AES_256_GCM_SHA384]:
        conversation = Connect("localhost", 4433)
        node = conversation
        ciphers = [cipher]
        node = node.add_child(ClientHelloGenerator(ciphers,
                                                   version=(3, 2),
                                                   extensions={ExtensionType.
                                                       renegotiation_info:None}))
        node = node.add_child(ExpectAlert())
        node.next_sibling = ExpectClose()

        conversations[CipherSuite.ietfNames[cipher] + " in TLSv1.1"] =\
                conversation

    good = 0
    bad = 0

    for conversation_name, conversation in conversations.items():
        print("{0} ...".format(conversation_name))

        runner = Runner(conversation)

        res = True
        try:
            runner.run()
        except:
            print("Error while processing")
            print(traceback.format_exc())
            print("")
            res = False

        if res:
            good+=1
            print("OK\n")
        else:
            bad+=1

    print("Test end")
    print("successful: {0}".format(good))
    print("failed: {0}".format(bad))

    if bad > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
