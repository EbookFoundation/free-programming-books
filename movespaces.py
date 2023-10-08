# Function to move spaces to front of string 
# in single traversal in Python 

def moveSpaces(input): 
	
	# Traverse string to create string without spaces 
	noSpaces = [ch for ch in input if ch!=' '] 

	# calculate number of spaces 
	space= len(input) - len(noSpaces) 

	# create result string with spaces 
	result = ' '*space 

	# concatenate spaces with string having no spaces 
	result = '"'+result + ''.join(noSpaces)+'"'
	print (result) 

# Driver program 
if __name__ == "__main__": 
	input = 'Utsav and Utsav'
	moveSpaces(input) 
