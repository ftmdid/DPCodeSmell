from collections import Counter
def sockMerchant(n, ar):
    counterEl =Counter(ar)
    counterList=[]
    for each in counterEl:
        if counterEl[each]>=2:
            counterList.append(int(counterEl[each]/2))
    count=0
    for each in counterList:
        count += each  
    return count
            

if __name__ == '__main__':

    n = int(input())

    ar = list(map(int, input().rstrip().split()))

    result = sockMerchant(n, ar)

    print(str(result) + '\n')

  