file = open('locations.txt', 'r') 
Lines = file.readlines()
numbers = ["0","1","2","3","4","5","6","7","8","9"]
input_x_width = 360
input_y_width = 185
output_x_width = 490
output_y_width = 252
offset_x = 10
offset_y = 10

name = "rajya_sabha"

failed_for = []
linenumber = 1

for line in Lines:
    size = len(line)
    x = ""
    y = ""
    x_dec = ""
    y_dec = ""
    state = 0
    n = 0
    endloop = 0
    
    while n < size :
        if state == 0:
            if line[n:n+7] == '<circle':
                state = 1
                n = n+6

        elif state == 1:
            if line[n:n+4] == 'cx="':
                state = 2
                n = n+3

        elif state == 2:
            if line[n] in numbers :
                x = x+line[n]
            elif line[n] == '.' :
                state = 7
            elif line[n] == '"' :
                state = 3
            else :
                state = 6

        elif state == 7:
            if line[n] in numbers :
                x_dec = x_dec+line[n]
            elif line[n] == '"' :
                state = 3
            else :
                state = 6

        elif state == 3:
            if line[n:n+4] == 'cy="':
                state = 4
                n = n+3

        elif state == 4:
            if line[n] in numbers :
                y = y+line[n]
            elif line[n] == '.' :
                state = 8
            elif line[n] == '"' :
                state = 5
                n = size
            else :
                state = 6

        elif state == 8:
            if line[n] in numbers :
                y_dec = y_dec+line[n]
            elif line[n] == '"' :
                state = 5
            else :
                state = 6
        
        n = n+1

    if state == 5:
        x = int(x)
        dec_size = len(x_dec)
        x_dec = int(x_dec)/10**(dec_size)
        x = x + x_dec
        x = round(x*output_x_width/input_x_width + offset_x,3)
        print('add_to_array = { '+name+'_x =',x,'}')
                  
        y = int(y)
        dec_size = len(y_dec)
        y_dec = int(y_dec)/10**(dec_size)
        y = y + y_dec
        y = round(y*output_y_width/input_y_width + offset_y,3)
        print('add_to_array = { '+name+'_y =',y,'}')
        

    else:
        failed_for.append(linenumber)
        
    linenumber = linenumber + 1

print("Failed for: ", failed_for)

    
         
