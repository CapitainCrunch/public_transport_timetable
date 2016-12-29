class DLdistance(object):
    def __init__(self, str1, str2):
        self.str1 = str1.lower()
        self.str2 = str2.lower()
        
    def distance(self):
        n1, n2 = len(self.str1), len(self.str2)
        max_dis = n1 + n2
        letters = {}
        init_pos = 2
        origin = init_pos - 1
        matrix = [[max_dis for _ in range(n1 + init_pos)] for _ in range(n2 + init_pos)]
        for i1 in range(origin, n1 + init_pos):
            matrix[1][i1] = i1-origin
        for i2 in range(origin, n2 + init_pos):
            matrix[i2][1] = i2-origin
        for i2 in range(init_pos, n2 + init_pos):
            temp = origin
            for i1 in range(init_pos, n1 + init_pos):
                p2 = letters.get(self.str1[i1-init_pos], origin)
                p1 = temp
                cost = 0 if self.str1[i1-init_pos] == self.str2[i2-init_pos] else 1
                if not cost:
                    temp = i1
                elem = min(matrix[i2-1][i1] + 1,
                            matrix[i2][i1-1] + 1,
                            matrix[i2-1][i1-1] + cost,
                            matrix[p2-1][p1-1] + 1 + (i1-p1-1) + (i2-p2-1) )
                matrix[i2][i1] = elem
            letters[self.str2[i2-init_pos]] = i2
        return matrix[-1][-1]

if __name__ == '__main__':
    print(DLdistance('Qqq', 'qqq').distance())