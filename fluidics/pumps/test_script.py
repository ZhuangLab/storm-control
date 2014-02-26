#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# The basic I/O class for a Rainin RP1 peristaltic pump
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import serial
import time

serial = serial.Serial(port = 4,
                       baudrate = 19200,
                       bytesize = serial.EIGHTBITS,
                       parity = serial.PARITY_EVEN,
                       stopbits = serial.STOPBITS_ONE,
                       timeout = 0.1)

print serial
print "Sending disconnect signal"
serial.write(chr(255))
print (serial.read(10), '')

time.sleep(0.1)

print "Sending Connect Signal to Device: " + str(30)
serial.write(chr(128 + 30))
time.sleep(0.1)
response = serial.read(1)
print "Received: " + str(ord(response) - 128)


#----------------------------------------------------------------------------------
# Testing Immediate Commands
#----------------------------------------------------------------------------------
print "Testing Immediate Commands"
print '\n'

# Read pump display
print "Reading Pump Display"
serial.write(chr( ord('R')))
print "Write: " + "R"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)

# Get Pump ID
print "Getting Pump ID"
serial.write(chr( ord('%')))
print "Write: " + "%"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)

# Get Pump Status
print "Getting Pump Status"
serial.write(chr( ord('?')))
print "Write: " + "?"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)

#----------------------------------------------------------------------------------
# Testing Buffered Commands
#----------------------------------------------------------------------------------
print "----------------------------------------------------------------------------"
print "Testing Buffered Commands"
print '\n'

# Check initial Pump Status
print "Getting Pump Status"
serial.write(chr( ord('?')))
print "Write: " + "?"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)

# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)

# Enter lock mode
message_to_write = [chr(ord('L')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        time.sleep(1)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))

# See if status has changed
print "Getting Pump Status"
serial.write(chr( ord('?')))
print "Write: " + "?"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)


# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)

# Change Speed
message_to_write = [chr(ord('R')), chr(ord('1')), chr(ord('0')), chr(ord('0')), chr(ord('0')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))

# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)


# Start Pump
message_to_write = [chr(ord('j')), chr(ord('F')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))

time.sleep(5)

# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)

# Change Speed
message_to_write = [chr(ord('R')), chr(ord('3')), chr(ord('0')), chr(ord('0')), chr(ord('0')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))

time.sleep(5)
# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)

# Change Speed
message_to_write = [chr(ord('R')), chr(ord('0')), chr(ord('0')), chr(ord('0')), chr(ord('0')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))


# Poll pump for ready signal
ready = False
ready_signal = '\n'
not_ready_signal = chr(ord('#'))
print "Is pump ready for buffered command?"
while not ready:
    serial.write('\x0A')
    response = serial.read(1)
    if response == ready_signal:
        ready = True
        print "Pump is ready to received buffered command"
        # Clear buffer
        response = serial.read(10)

# Enter lock mode
message_to_write = [chr(ord('U')), '\x0D']

print "Writing: " + str(message_to_write)

for message in message_to_write:
    received = False
    while not received:
        print "Writing: " + message
        serial.write(message)
        time.sleep(1)
        response = serial.read(10)
        print "Response: " + str((response, ''))
        if response == message:
            received = True
        else:
            print "Error in transmission of " + str((message, ''))

# See if status has changed
print "Getting Pump Status"
serial.write(chr( ord('?')))
print "Write: " + "?"
done = False
complete_message = []
while not done:
    response = serial.read(1)
    #print (response, ord(response))
    if ord(response) > 128:
        done = True
        print "Triggered complete"
        complete_message.append( chr(ord(response)-128))
    else:
        complete_message.append(response)
        serial.write(chr(6))

print "Received: " + str(complete_message)



### Poll pump for ready signal
##ready = False
##while not ready:
##    serial.write('\x0A')
##    print "Writing: " + '\x0A'
##    response = serial.read(1)
##    print "Response: " + str((response, ''))
##    if response == ready_signal:
##        ready = True
##        print "Pump is ready to received buffered command"

##
### Change pump speed
##message_to_write = ['\x0A', chr(ord('R')), chr(ord('1')), chr(ord('0')), chr(ord('0')), chr(ord('0')), '\x0D'];
##for message in message_to_write:
##    received = False
##    while not received:
##        print "Writing: " + message
##        serial.write(message)
##        time.sleep(1)
##        response = serial.read(10)
##        print "Response: " + str((response, ''))
##        if response == message:
##            received = True
##        else:
##            print "Error in transmission of " + str((message, ''))
