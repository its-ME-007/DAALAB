arr = [1,2,3,4,5]
lo = 0
hi = len(arr)-1
mid = 0

while (lo<=hi): 
	mid += (lo+hi)//2
	if (arr[mid] == 2): 
		print(arr[mid])
		break
	elif(arr[mid] > 2):
		hi = mid-1
	else:
		lo = mid+1