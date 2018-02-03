from file_formats.m2_format import M2Header

if __name__ == '__main__':
    with open("C:\\users\\sshum\\desktop\\8tr_amani_gong01.m2", 'rb') as f:
        m2 = M2Header()
        m2.__read__(f)