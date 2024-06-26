
#Measure depth of dictionary
def dict_depth(dic, level = 1):
     
    if not isinstance(dic, dict) or not dic:
        return level
    return max(dict_depth(dic[key], level + 1)
                               for key in dic)