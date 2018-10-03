def remove_dupes(mylist):
    """
        Basic deduping function to remove any duplicates from a list
    """
    if len(mylist) > 0:
        newlist = [mylist[0]]
        for e in mylist:
            if e not in newlist:
                newlist.append(e)
        return newlist
    return mylist